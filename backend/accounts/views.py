"""
Authentication Views for Accounts.
"""
import logging
import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.mail import send_mail
from .models import EmailVerificationToken

from rest_framework import serializers as drf_serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from drf_spectacular.utils import extend_schema

from .serializers import RegisterSerializer
from .throttles import (
    LoginRateThrottle,
    RegisterRateThrottle,
    GoogleLoginRateThrottle,
)

logger = logging.getLogger("accounts")
User = get_user_model()

def _set_refresh_cookie(response, refresh_token_str: str) -> None:
    """
    Attach the refresh token as an HttpOnly cookie.
    """
    response.set_cookie(
        key=settings.JWT_AUTH_COOKIE,
        value=refresh_token_str,
        max_age=settings.JWT_AUTH_COOKIE_MAX_AGE,
        httponly=settings.JWT_AUTH_COOKIE_HTTPONLY,
        secure=settings.JWT_AUTH_COOKIE_SECURE,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        path='/',
    )


def _clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        key=settings.JWT_AUTH_COOKIE,
        path='/',
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
    )


def _generic_error(msg="A server error occurred.", http_status=status.HTTP_500_INTERNAL_SERVER_ERROR):
    return Response({"success": False, "message": msg}, status=http_status)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = drf_serializers.EmailField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].allow_blank = True

    def validate(self, attrs):
        if attrs.get("email") and not attrs.get("username"):
            attrs["username"] = attrs["email"].lower()
        data = super().validate(attrs)
        try:
            if not self.user.emailverificationtoken.verified:
                raise drf_serializers.ValidationError("Please verify your email before logging in.")
        except EmailVerificationToken.DoesNotExist:
            pass
        return data


@extend_schema(tags=["Auth"], summary="JWT login")
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken) as e:
            logger.warning("Login failed for data=%s reason=%s", request.data.get("email"), str(e))
            return Response(
                {"success": False, "detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data
        refresh_str = data.get("refresh", "")
        access_str = data.get("access", "")

        response = Response(
            {"success": True, "access": access_str},
            status=status.HTTP_200_OK,
        )
        _set_refresh_cookie(response, refresh_str)
        return response


@extend_schema(tags=["Auth"], summary="Register a new user")
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user = serializer.save()
                frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
                token_obj, _ = EmailVerificationToken.objects.get_or_create(user=user)
                verify_link = f"{frontend_url}/verify-email/{token_obj.token}/"
                print(f"[VERIFICATION LINK] User: {user.email} -> {verify_link}", flush=True)
                logger.info("[VERIFICATION LINK] User: %s -> %s", user.email, verify_link)
                
                subject = "Verify your Ingrexa account"
                body = f"Click the link to verify your account: {verify_link}"
                email_sent = False
                
                try:
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    email_sent = True
                    logger.info("Verification email sent via SMTP to %s", user.email)
                except Exception as smtp_err:
                    logger.warning("SMTP verification email failed: %s. Trying Resend API...", smtp_err)
                
                if not email_sent:
                    import requests as http_requests
                    resend_api_key = os.environ.get('RESEND_API_KEY', '')
                    if resend_api_key:
                        resp = http_requests.post(
                            'https://api.resend.com/emails',
                            headers={
                                'Authorization': f'Bearer {resend_api_key}',
                                'Content-Type': 'application/json'
                            },
                            json={
                                'from': 'Ingrexa Verification <onboarding@resend.dev>',
                                'to': [user.email],
                                'subject': subject,
                                'text': body
                            },
                            timeout=10,
                        )
                        if resp.status_code in [200, 201, 202]:
                            email_sent = True
                            logger.info("Verification email sent via Resend API to %s", user.email)
                        else:
                            logger.error("Resend API failed with status %s: %s", resp.status_code, resp.text)
                    else:
                        logger.warning("No Resend API key configured for fallback.")
        except Exception as e:
            logger.error("Registration error: %s", str(e), exc_info=True)
            return _generic_error("Registration failed. Please try again.")

        return Response(
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Auth"], summary="Refresh access token")
class CookieTokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Reads the refresh token from cookie and returns a new access token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_str = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if not refresh_str:
            return Response(
                {"success": False, "detail": "Refresh token missing."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(refresh_str)
            access_str = str(refresh.access_token)
            new_refresh_str = str(refresh)
        except TokenError as e:
            logger.info("Refresh token invalid/expired: %s", str(e))
            response = Response(
                {"success": False, "detail": "Session expired. Please log in again."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            _clear_refresh_cookie(response)
            return response

        response = Response({"success": True, "access": access_str}, status=status.HTTP_200_OK)
        _set_refresh_cookie(response, new_refresh_str)
        return response


@extend_schema(tags=["Auth"], summary="Logout — clear refresh cookie")
class LogoutAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Blacklist the refresh token and clear the cookie."""
        refresh_str = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if refresh_str:
            try:
                RefreshToken(refresh_str).blacklist()
            except Exception:
                pass  # Already expired / invalid — still clear cookie

        response = Response({"success": True, "message": "Logged out."}, status=status.HTTP_200_OK)
        _clear_refresh_cookie(response)
        return response


@extend_schema(tags=["Auth"], summary="Get current user profile")
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            from analyzer.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            return Response(
                {
                    "success": True,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "health_goal": profile.health_goal or "General Health",
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.error("Profile fetch error", exc_info=True)
            return _generic_error("Unable to retrieve profile.")

    def patch(self, request):
        try:
            from analyzer.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            if "health_goal" in request.data:
                profile.health_goal = request.data["health_goal"]
                profile.save()
            return Response({"success": True, "health_goal": profile.health_goal})
        except Exception:
            logger.error("Profile update error", exc_info=True)
            return _generic_error("Unable to update profile.")


@extend_schema(tags=["Auth"], summary="Login with Google")
class GoogleLoginAPIView(APIView):
    """
    Handle Google OAuth login.
    Supports credential ID tokens and access tokens.
    """
    permission_classes = [AllowAny]
    throttle_classes = [GoogleLoginRateThrottle]

    def post(self, request):
        credential = request.data.get("credential")
        access_token = request.data.get("access_token")
        nonce = request.data.get("nonce", "")

        if not credential and not access_token:
            return Response(
                {"success": False, "message": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            email, first_name, last_name = None, "", ""

            if credential:
                import requests as py_requests
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests

                client_id = os.environ.get("GOOGLE_CLIENT_ID")
                idinfo = id_token.verify_oauth2_token(
                    credential, google_requests.Request(), client_id
                )

                if nonce:
                    token_nonce = idinfo.get("nonce", "")
                    if not secrets.compare_digest(nonce, token_nonce):
                        logger.warning("Google OAuth nonce mismatch from %s", request.META.get("REMOTE_ADDR"))
                        return Response(
                            {"success": False, "message": "Authentication failed."},
                            status=status.HTTP_401_UNAUTHORIZED,
                        )

                email = idinfo["email"]
                first_name = idinfo.get("given_name", "")
                last_name = idinfo.get("family_name", "")

            else:
                import requests as py_requests
                userinfo_res = py_requests.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10,
                )
                if not userinfo_res.ok:
                    raise ValueError("Failed to verify access token with Google.")
                user_data = userinfo_res.json()
                email = user_data["email"]
                first_name = user_data.get("given_name", "")
                last_name = user_data.get("family_name", "")

            username = email.lower()

            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )
                if created:
                    user.set_unusable_password()
                    user.save()
                    from analyzer.models import UserProfile
                    UserProfile.objects.get_or_create(user=user)

            refresh = RefreshToken.for_user(user)
            access_str = str(refresh.access_token)
            refresh_str = str(refresh)

            response = Response(
                {
                    "success": True,
                    "access": access_str,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                    },
                },
                status=status.HTTP_200_OK,
            )
            _set_refresh_cookie(response, refresh_str)
            return response

        except Exception:
            logger.error("Google Login error", exc_info=True)
            return Response(
                {"success": False, "message": "Authentication failed."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

@extend_schema(tags=["Auth"], summary="Verify email address via token")
class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            token_obj = EmailVerificationToken.objects.get(token=token)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid verification link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token_obj.verified:
            return Response(
                {"success": True, "message": "Email already verified."},
                status=status.HTTP_200_OK,
            )

        if token_obj.is_expired():
            return Response(
                {"success": False, "message": "Verification link has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_obj.verified = True
        token_obj.save()

        return Response(
            {"success": True, "message": "Email verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )
    from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

class AdditiveListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        additives_data = [
            {"id": 1, "name": "Aspartame", "role": "Artificial Sweetener", "status": "Caution", "description": "Common zero-calorie sweetener. Contains phenylalanine; dangerous for individuals with PKU and a known trigger for migraines or gut sensitivity in some people."},
            {"id": 2, "name": "Artificial Colorings (Allura Red / Tartrazine)", "role": "Coloring Agent", "status": "Avoid", "description": "Petroleum-derived synthetic dyes. Highly scrutinized for links to hyperactivity in children and potential mild allergic/histamine reactions."},
            {"id": 3, "name": "Butylated Hydroxyanisole (BHA)", "role": "Preservative", "status": "Avoid", "description": "Synthetic antioxidant used to prevent fats from spoiling. Listed as a suspected endocrine disruptor and anticipated human carcinogen."},
            {"id": 4, "name": "Bleached Flour Agents (Benzoyl Peroxide)", "role": "Flour Treatment", "status": "Caution", "description": "Used to whiten wheat flour. Severely strips natural nutrients and often masks highly processed, gluten-heavy refined grain foods."},
            {"id": 5, "name": "Casein / Caseinate", "role": "Emulsifier / Texture Modifier", "status": "Avoid", "description": "🚨 DAIRY ALLERGEN. A major milk protein used to improve texture in processed meats and non-dairy creamers. High risk for dairy allergy sufferers."},
            {"id": 6, "name": "Carrageenan", "role": "Thickener / Stabilizer", "status": "Caution", "description": "Seaweed extract used widely in dairy alternatives. Extensively debated for causing gut inflammation, bloating, and altering microbiome health."},
            {"id": 7, "name": "Dextrin / Maltodextrin", "role": "Thickener / Bulking Agent", "status": "Caution", "description": "🚨 GLUTEN RISK. Highly processed starch usually made from corn, but sometimes derived from wheat. Spikes blood sugar rapidly due to high glycemic index."},
            {"id": 8, "name": "Diacetyl", "role": "Artificial Flavoring", "status": "Avoid", "description": "Chemical mimicking buttery flavor. While ingested safely in small amounts, it is linked to severe respiratory inflammation when processed or inhaled."},
            {"id": 9, "name": "Erythritol", "role": "Sugar Alcohol Sweetener", "status": "Caution", "description": "Bulk low-calorie sweetener. Frequently causes digestive distress, gas, and cramping when consumed in moderate to high quantities."},
            {"id": 10, "name": "Ethylenediamine Tetraacetic Acid (EDTA)", "role": "Preservative / Chelating Agent", "status": "Caution", "description": "Used to bind minerals and prevent flavor degradation. Can cause mineral binding imbalances if consumed excessively over long periods."},
            {"id": 11, "name": "Fructose (High Fructose Corn Syrup)", "role": "Sweetener", "status": "Avoid", "description": "Highly processed corn syrup derivative. Strongly linked to fatty liver disease, type-2 diabetes, obesity, and metabolic syndrome."},
            {"id": 12, "name": "Fumaric Acid", "role": "Acidity Regulator", "status": "Safe", "description": "Naturally occurring organic acid used to add sour notes to rye breads and tart candies. Generally safe and non-toxic."},
            {"id": 13, "name": "Guar Gum", "role": "Thickener / Emulsifier", "status": "Caution", "description": "Seed-derived fiber used in sauces and ice creams. Can trigger gas, loose stools, and abdominal discomfort in individuals with sensitive guts."},
            {"id": 14, "name": "Gluten (Vital Wheat Gluten Additive)", "role": "Binder / Texturizer", "status": "Avoid", "description": "🚨 GLUTEN ALLERGEN. Pure wheat protein isolated and added to low-protein flours and meat substitutes. Triggers severe autoimmune response in Celiac disease."},
            {"id": 15, "name": "Hydrolyzed Vegetable Protein (HVP)", "role": "Flavor Enhancer", "status": "Caution", "description": "🚨 GLUTEN / SOY RISK. Chemically broken-down plant protein often made from wheat or soy. Contains hidden naturally occurring monosodium glutamate (MSG)."},
            {"id": 16, "name": "Hexane-Processed Soy Isolates", "role": "Protein Supplement / Texturizer", "status": "Avoid", "description": "🚨 SOY ALLERGEN. Soy protein extracted using chemical solvents like hexane. Known allergen base used heavily in protein bars and meat analogues."},
            {"id": 17, "name": "Invert Sugar Syrup", "role": "Sweetener", "status": "Avoid", "description": "Sucrose split into glucose and fructose. Used to keep baked goods moist, but acts as an added fast-absorbing refined sugar that causes insulin spikes."},
            {"id": 18, "name": "Inosinate (Disodium Inosinate)", "role": "Flavor Enhancer", "status": "Caution", "description": "Synergistic savory chemical modifier often paired directly with MSG. Individuals tracking gout or purine restrictions should avoid it."},
            {"id": 19, "name": "Juice Concentrates (Deionized)", "role": "Sweetener", "status": "Caution", "description": "Fruit juice stripped of its natural minerals, flavors, and fibers. Functions purely as a hidden, concentrated layout sugar substitute."},
            {"id": 20, "name": "Juniper Extract", "role": "Natural Flavoring Agent", "status": "Safe", "description": "Botanical aromatic extract used primarily in beverages. Generally non-toxic, though rare contact or ingestion sensitivities can happen."},
            {"id": 21, "name": "Karaya Gum", "role": "Thickener / Laxative Binder", "status": "Caution", "description": "Natural tree exudate gum. Used in dressings and spreads. Known to cause mild laxative effects and allergic reactions in specific cohorts."},
            {"id": 22, "name": "Konjac Flour / Glucomannan", "role": "Gelling Agent / Thickener", "status": "Safe", "description": "Extremely dense dietary soluble fiber matrix. Generally safe but creates choking risks if used in firm, bite-sized jelly treats."},
            {"id": 23, "name": "Lactose", "role": "Bulking Filler / Sweetener", "status": "Avoid", "description": "🚨 DAIRY ALLERGEN. Milk sugar crystallization derivative. Triggers heavy digestive upset, gas, and cramping for lactose intolerant individuals."},
            {"id": 24, "name": "Lecithin (Soy-derived)", "role": "Emulsifier", "status": "Caution", "description": "🚨 SOY RISK. Keeps fats and water mixed uniformly. Most soy lecithin is processed enough to lack soy proteins, but highly sensitive allergy types should check sources."},
            {"id": 25, "name": "Monosodium Glutamate (MSG)", "role": "Flavor Enhancer", "status": "Caution", "description": "Amino acid salt providing savory umami flavor. Regarded safe globally, but can cause temporary headaches or flushing in sensitive subsets."},
            {"id": 26, "name": "Modified Food Starch", "role": "Thickener", "status": "Caution", "description": "🚨 GLUTEN RISK. Chemically modified plant carbohydrate. If derived from wheat without explicit labeling, it poses a hidden risk for Celiac sufferers."},
            {"id": 27, "name": "Natamycin", "role": "Antifungal Preservative", "status": "Caution", "description": "🚨 DAIRY COATING. An antifungal agent applied to the rind of cheeses to prevent mold growth. Can trigger responses in individuals highly sensitive to mold or dairy derivatives."},
            {"id": 28, "name": "Neotame", "role": "Artificial Sweetener", "status": "Caution", "description": "Ultra-potent artificial sweetener derived from aspartame structure. Chemically stable but heavily synthesized and processed."},
            {"id": 29, "name": "Oat Fiber (Uncertified)", "role": "Bulking Texturizer", "status": "Caution", "description": "🚨 GLUTEN RISK. Added dietary fiber. Unless certified gluten-free, oats suffer massive cross-contamination from wheat during agricultural harvesting."},
            {"id": 30, "name": "Oleoresins", "role": "Concentrated Spice Extract", "status": "Safe", "description": "Natural plant spice extract residues used for standardizing color and flavor profiles. Clean and safe unless specific spice allergies exist."},
            {"id": 31, "name": "Potassium Bromate", "role": "Flour Maturing Enhancer", "status": "Avoid", "description": "Oxidizing agent used to strengthen bread dough structure. Banned in many countries due to potential carcinogenic properties if baked incorrectly."},
            {"id": 32, "name": "Polysorbate 60 / 80", "role": "Emulsifier", "status": "Avoid", "description": "Synthetic compounds used to keep ice cream and baked goods creamy. Suspected of shifting healthy gut microflora and degrading gut lining layers."},
            {"id": 33, "name": "Quillaia Saponins", "role": "Foaming Agent", "status": "Caution", "description": "Natural bark extract used to create foam headers in soft drinks like root beer. Safe in low limits but acts as a heavy local throat irritant if concentrated."},
            {"id": 34, "name": "Quinoline Yellow", "role": "Synthetic Dye", "status": "Avoid", "description": "Coal-tar derived artificial color hue. Heavily restricted or banned in multiple global regions due to asthma and hyperactivity links in minors."},
            {"id": 35, "name": "Red 40 (Allura Red AC)", "role": "Artificial Color", "status": "Avoid", "description": "Extremely common petroleum-derived red dye. Extensively monitored for links to behavioral shifts, focus reduction, and hives in children."},
            {"id": 36, "name": "Rice Malt Syrup", "role": "Sweetener", "status": "Caution", "description": "Alternative sweetener made by breaking down rice starch. Completely fructose-free, but possesses a sky-high glycemic index that spikes insulin."},
            {"id": 37, "name": "Sodium Benzoate", "role": "Preservative", "status": "Caution", "description": "Inhibits mold growth in acidic foods. Can convert into benzene (a known carcinogen) if combined directly inside formula drinks with Vitamin C."},
            {"id": 38, "name": "Sodium Metabisulfite", "role": "Sulfite Preservative", "status": "Avoid", "description": "🚨 SULFITE ALLERGEN. Chemical bleaching and preservation agent. Known to trigger acute asthma attacks and heavy respiratory reactions in sulfite-allergic groups."},
            {"id": 39, "name": "Tartrazine (Yellow 5)", "role": "Artificial Color", "status": "Avoid", "description": "Bright yellow azo dye. Noted for inducing aspirin-like allergy responses, asthma breathing issues, and hives in susceptible individuals."},
            {"id": 40, "name": "Textured Vegetable Protein (TVP)", "role": "Meat Substitute Filler", "status": "Avoid", "description": "🚨 SOY / GLUTEN ALLERGEN. Manufactured plant extract made largely from defatted soy flour. Heavy trigger base for consumers tracking legume sensitivities."},
            {"id": 41, "name": "Unbleached Wheat Flour Additive", "role": "Refined Base Grain", "status": "Avoid", "description": "🚨 GLUTEN ALLERGEN. Standard enriched grain base. Contains natural concentrations of gluten proteins, causing immediate digestive distress to Celiac patients."},
            {"id": 42, "name": "Urea", "role": "Fermentation Nutrient", "status": "Safe", "description": "Nitrogen compound used as a yeast food source during heavy commercial alcohol processing. Safely consumed when restricted within regulatory parameters."},
            {"id": 43, "name": "Vegetable Oil (Partially Hydrogenated)", "role": "Fat Emollient / Oil Base", "status": "Avoid", "description": "The technical classification source for harmful industrial Trans Fats. Directly raises LDL (bad) cholesterol and significantly increases coronary heart disease risks."},
            {"id": 44, "name": "Vanillin (Ethyl Vanillin Synthetic)", "role": "Artificial Flavoring", "status": "Safe", "description": "Lab-synthesized alternative to natural vanilla extract beans. Highly consistent, cost-effective, and safe for standard consumer intake."},
            {"id": 45, "name": "Whey Protein Concentrate", "role": "Protein Filler / Texturizer", "status": "Avoid", "description": "🚨 DAIRY ALLERGEN. Liquid milk byproduct powder. Heavily rich in residual lactose and dairy proteins, causing immediate bloating or allergic flare-ups."},
            {"id": 46, "name": "Wheat Starch", "role": "Thickening Binder", "status": "Avoid", "description": "🚨 GLUTEN ALLERGEN. Carbohydrate matrix isolated from wheat plants. Frequently holds trace amounts of gluten fractions unless certified gluten-isolated."},
            {"id": 47, "name": "Xanthan Gum", "role": "Stabilizer / Thickener", "status": "Caution", "description": "Bacterial fermentation sugar product. Widely utilized in gluten-free baking, but known to trigger gas, bloating, and mild digestive shifts if overconsumed."},
            {"id": 48, "name": "Xylitol", "role": "Sugar Alcohol Sweetener", "status": "Caution", "description": "Plant-derived sugar alcohol. Causes dramatic gastrointestinal distress or laxative effects in humans if over-eaten. (Extremely toxic to pets)."},
            {"id": 49, "name": "Yeast Extract (Autolyzed)", "role": "Flavor Enhancer", "status": "Caution", "description": "🚨 GLUTEN RISK. Savory concentrated extract containing rich free glutamates. Often grown on barley crops, presenting a cross-contamination hazard for gluten sensitivity."},
            {"id": 50, "name": "Yellow 6 (Sunset Yellow FCF)", "role": "Synthetic Color dye", "status": "Avoid", "description": "Artificial chemical coloring compound. Highly monitored across Europe due to suspected connections with asthma, allergies, and skin rashes."},
            {"id": 51, "name": "Zein", "role": "Glaze Glosser / Coating agent", "status": "Safe", "description": "Corn-extracted protein powder used to coat vitamin tablets and candies. Naturally gluten-free and easily processed by the human metabolic system."},
            {"id": 52, "name": "Zinc Oxide Additive", "role": "Nutrient Fortifier", "status": "Safe", "description": "Mineral additive used to artificially fortify refined breakfast cereals. Completely safe and highly effective at addressing zinc deficiencies."}
        ]
        return Response(additives_data, status=status.HTTP_200_OK)

__all__ = [
    "RegisterAPIView",
    "MeAPIView",
    "EmailTokenObtainPairView",
    "VerifyEmailAPIView",
    "CookieTokenRefreshView",
    "LogoutAPIView",
    "GoogleLoginAPIView",
]
