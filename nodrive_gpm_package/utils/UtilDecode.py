import hmac
import hashlib
import base64
import time
import re


def code2Fa(secretKey) -> str:
    """
    Universal 2FA TOTP code generator that handles multiple secret key formats:
    - With spaces: "i2cr nkm5 ekfo tsqa 7fhy xjpd m7yi yhzi"
    - Without spaces: "R4JG2YN7UT37K7QDWATZBY5X6NBKISUX"
    - With dashes, lowercase, etc.
    """
    try:
        # ===== DETECT AND CLEAN SECRET KEY FORMAT =====
        original_secret = secretKey
        print(f"Original secret: '{original_secret}'")

        # Step 1: Remove all non-alphanumeric characters and normalize
        cleaned_secret = re.sub(r"[^A-Za-z0-9]", "", secretKey).upper()
        print(f"After cleaning: '{cleaned_secret}' (length: {len(cleaned_secret)})")

        # Step 2: Validate base32 characters (A-Z, 2-7 only)
        valid_base32_pattern = re.compile(r"^[A-Z2-7]*$")
        if not valid_base32_pattern.match(cleaned_secret):
            # Remove any invalid base32 characters
            cleaned_secret = re.sub(r"[^A-Z2-7]", "", cleaned_secret)
            print(f"After removing invalid base32 chars: '{cleaned_secret}'")

        # Step 3: Handle base32 padding properly
        # Base32 strings should be multiples of 8 characters
        remainder = len(cleaned_secret) % 8
        if remainder != 0:
            padding_needed = 8 - remainder
            cleaned_secret += "=" * padding_needed
            print(f"Added {padding_needed} padding chars: '{cleaned_secret}'")

        # ===== VALIDATE FINAL SECRET =====
        if len(cleaned_secret) < 8:
            raise ValueError(
                f"Secret too short after cleaning: {len(cleaned_secret)} chars"
            )

        # ===== DECODE AND GENERATE TOTP =====
        try:
            # Decode base32 secret
            secret_bytes = base64.b32decode(cleaned_secret)
            print(f"Secret decoded: {len(secret_bytes)} bytes")
        except Exception as decode_error:
            print(f"Base32 decode error: {decode_error}")
            # Try alternative decoding with casefold
            secret_bytes = base64.b32decode(cleaned_secret, casefold=True)
            print(f"Secret decoded with casefold: {len(secret_bytes)} bytes")

        # Calculate time counter (30-second window)
        current_time = int(time.time())
        counter = current_time // 30
        counter_bytes = counter.to_bytes(8, byteorder="big")
        print(f"Time: {current_time}, Counter: {counter}")

        # Generate HMAC-SHA1
        hmac_hash = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation to get 6-digit code
        offset = hmac_hash[-1] & 0x0F
        code_bytes = hmac_hash[offset : offset + 4]
        code_int = int.from_bytes(code_bytes, byteorder="big") & 0x7FFFFFFF
        totp_code = code_int % 1000000

        # Format as 6-digit string with leading zeros
        result = f"{totp_code:06d}"
        print(f"✅ Generated 2FA code: {result}")

        return result

    except Exception as e:
        print(f"❌ Error generating 2FA code: {e}")
        return None
