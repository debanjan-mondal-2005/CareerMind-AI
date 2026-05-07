import os
import resend # pyright: ignore[reportMissingImports]
from dotenv import load_dotenv


load_dotenv()


def send_registration_email(to_email, first_name, student_key):
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "CareerMind AI <noreply@mail.debanjan.me>")

    if not resend_api_key:
        return {
            "success": False,
            "message": "RESEND_API_KEY not found in .env file"
        }

    resend.api_key = resend_api_key

    subject = "Welcome to CareerMind AI 🚀 - Your Journey Starts Here"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.8; color: #333;">
        <h2 style="color: #6366f1;">Welcome to CareerMind AI, {first_name}! 🎯</h2>

        <p style="font-size: 16px;">
            Your account has been created successfully! You're now part of a community of students 
            building amazing careers with the help of AI mentorship.
        </p>

        <div style="background-color: #f0f4ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #6366f1;">
            <p style="margin: 0; font-size: 14px; color: #666;">
                <strong>Your Login Credentials:</strong>
            </p>
            <p style="margin: 8px 0; font-size: 16px; font-family: monospace; background-color: white; padding: 10px; border-radius: 4px; color: #6366f1;">
                Student Key: <strong>{student_key}</strong>
            </p>
            <p style="margin: 8px 0; font-size: 14px; color: #666;">
                Password: The password you created during registration
            </p>
        </div>

        <p style="font-size: 16px;">
            <strong>Next Steps:</strong>
        </p>
        <ul style="font-size: 15px;">
            <li>Log in to CareerMind AI with your Student Key and password</li>
            <li>Complete your profile through the onboarding questions</li>
            <li>Start asking questions and get personalized career guidance</li>
        </ul>

        <p style="font-size: 15px; color: #666;">
            <strong>🔒 Security Tip:</strong> Never share your password with anyone. 
            Keep your Student Key safe as you'll need it to log in.
        </p>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="font-size: 14px; color: #999;">
            Questions? Visit our support center or reply to this email.
            <br><br>
            Best regards,<br>
            <strong>The CareerMind AI Team</strong> 🚀
        </p>
    </div>
    """

    try:
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        email_response = resend.Emails.send(params)

        return {
            "success": True,
            "message": "Registration email sent successfully",
            "email_response": email_response
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}"
        }