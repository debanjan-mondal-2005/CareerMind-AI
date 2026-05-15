import os
import resend # pyright: ignore[reportMissingImports]
from dotenv import load_dotenv


load_dotenv()


def send_registration_email(to_email, first_name, student_key):
    from datetime import datetime
    from database.db import SessionLocal, Student
    
    resend_api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "CareerMind AI <noreply@mail.debanjan.me>")

    db = SessionLocal()
    student = db.query(Student).filter(Student.email == to_email.strip().lower()).first()

    if not resend_api_key:
        if student:
            student.email_sent_status = "failed"
            db.commit()
        db.close()
        return {
            "success": False,
            "message": "RESEND_API_KEY not found in .env file"
        }

    resend.api_key = resend_api_key
    subject = "Your AI Career Mentor is Ready — Welcome to CareerMind AI! 🚀"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            @media only screen and (max-width: 600px) {{
                .container {{ width: 100% !important; padding: 20px !important; }}
                .feature-card {{ width: 100% !important; margin-bottom: 10px !important; }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; color: #1e293b;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);">
            <!-- Header -->
            <tr>
                <td style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); padding: 40px 20px; text-align: center;">
                    <div style="background-color: #ffffff; width: 60px; height: 60px; line-height: 60px; border-radius: 15px; margin: 0 auto 15px; color: #6366f1; font-size: 28px; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">CM</div>
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.025em;">CareerMind AI</h1>
                </td>
            </tr>

            <!-- Body -->
            <tr>
                <td style="padding: 40px 30px;">
                    <h2 style="margin: 0 0 16px; color: #1e293b; font-size: 22px; font-weight: 700;">Hello {first_name},</h2>
                    <p style="margin: 0 0 24px; font-size: 16px; line-height: 1.6; color: #475569;">
                        Your AI-powered career journey begins now. We're excited to help you navigate the future of work with personalized mentorship and industry-grade roadmaps.
                    </p>

                    <!-- Student Key Card -->
                    <div style="background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 32px;">
                        <p style="margin: 0 0 8px; font-size: 13px; font-weight: 600; color: #6366f1; text-transform: uppercase; letter-spacing: 0.05em;">Your Access Credentials</p>
                        <div style="background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 15px; margin-bottom: 12px; text-align: center;">
                            <span style="font-family: 'Courier New', Courier, monospace; font-size: 20px; font-weight: 800; color: #1e293b; letter-spacing: 2px;">{student_key}</span>
                        </div>
                        <p style="margin: 0; font-size: 14px; color: #64748b;">
                            Use this Student Key and the password you created to sign in.
                        </p>
                    </div>

                    <!-- Next Steps -->
                    <h3 style="margin: 0 0 16px; font-size: 18px; font-weight: 600; color: #1e293b;">Your Onboarding Roadmap</h3>
                    <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
                        <tr>
                            <td width="30" valign="top" style="padding-top: 5px;"><div style="width: 20px; height: 20px; background-color: #6366f1; color: #ffffff; border-radius: 50%; font-size: 12px; text-align: center; line-height: 20px;">1</div></td>
                            <td style="padding-bottom: 15px;"><strong style="color: #1e293b;">Login:</strong> Access the platform with your unique Key.</td>
                        </tr>
                        <tr>
                            <td width="30" valign="top" style="padding-top: 5px;"><div style="width: 20px; height: 20px; background-color: #6366f1; color: #ffffff; border-radius: 50%; font-size: 12px; text-align: center; line-height: 20px;">2</div></td>
                            <td style="padding-bottom: 15px;"><strong style="color: #1e293b;">Select Path:</strong> Choose between School or College flow.</td>
                        </tr>
                        <tr>
                            <td width="30" valign="top" style="padding-top: 5px;"><div style="width: 20px; height: 20px; background-color: #6366f1; color: #ffffff; border-radius: 50%; font-size: 12px; text-align: center; line-height: 20px;">3</div></td>
                            <td style="padding-bottom: 15px;"><strong style="color: #1e293b;">AI Setup:</strong> Answer a few questions to build your profile.</td>
                        </tr>
                        <tr>
                            <td width="30" valign="top" style="padding-top: 5px;"><div style="width: 20px; height: 20px; background-color: #6366f1; color: #ffffff; border-radius: 50%; font-size: 12px; text-align: center; line-height: 20px;">4</div></td>
                            <td><strong style="color: #1e293b;">Dashboard:</strong> Access your personalized mentorship hub.</td>
                        </tr>
                    </table>

                    <!-- CTA Button -->
                    <div style="text-align: center; margin-bottom: 32px;">
                        <a href="https://careermind-ai-three.vercel.app/" style="background-color: #6366f1; color: #ffffff; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);">Launch CareerMind AI</a>
                    </div>

                    <!-- Features -->
                    <div style="border-top: 1px solid #f1f5f9; padding-top: 32px;">
                        <h3 style="margin: 0 0 16px; font-size: 18px; font-weight: 600; color: #1e293b;">Platform Highlights</h3>
                        <table width="100%" border="0" cellpadding="0" cellspacing="0">
                            <tr>
                                <td width="50%" style="padding-right: 10px; padding-bottom: 15px;">
                                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; font-size: 14px;">
                                        <strong style="display: block; color: #6366f1; margin-bottom: 4px;">AI Mentorship</strong>
                                        24/7 expert career guidance.
                                    </div>
                                </td>
                                <td width="50%" style="padding-left: 10px; padding-bottom: 15px;">
                                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; font-size: 14px;">
                                        <strong style="display: block; color: #6366f1; margin-bottom: 4px;">Smart Roadmaps</strong>
                                        Personalized learning paths.
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td width="50%" style="padding-right: 10px;">
                                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; font-size: 14px;">
                                        <strong style="display: block; color: #6366f1; margin-bottom: 4px;">Project Ideas</strong>
                                        Industry-grade project suggestions.
                                    </div>
                                </td>
                                <td width="50%" style="padding-left: 10px;">
                                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; font-size: 14px;">
                                        <strong style="display: block; color: #6366f1; margin-bottom: 4px;">Skill Analysis</strong>
                                        Data-driven gap analysis.
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </div>
                </td>
            </tr>

            <!-- Footer Section -->
            <tr>
                <td style="background-color: #f8fafc; padding: 30px; text-align: center;">
                    <p style="margin: 0 0 12px; font-size: 14px; color: #64748b; font-weight: 600;">🔒 Security Note</p>
                    <p style="margin: 0 0 24px; font-size: 12px; line-height: 1.5; color: #94a3b8;">
                        Never share your password. Our team will never ask for your credentials. If you didn't create this account, please ignore this email.
                    </p>
                    <div style="border-top: 1px solid #e2e8f0; margin-bottom: 24px;"></div>
                    <p style="margin: 0; font-size: 13px; color: #64748b; font-weight: 600;">CareerMind AI Team</p>
                    <p style="margin: 4px 0 0; font-size: 12px; color: #94a3b8;">AI-Powered Career Mentorship Platform</p>
                    <p style="margin: 15px 0 0; font-size: 11px; color: #cbd5e1;">© 2026 CareerMind AI. All rights reserved.</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    try:
        params = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        email_response = resend.Emails.send(params)
        
        if student:
            student.email_sent_status = "sent"
            student.email_sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.commit()

        return {
            "success": True,
            "message": "Registration email sent successfully",
            "email_response": email_response
        }

    except Exception as e:
        if student:
            student.email_sent_status = "failed"
            db.commit()
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}"
        }
    finally:
        db.close()