import unittest

from app import app


class PdfReportTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.post(
            "/register",
            data={
                "email": "pdfuser@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
            follow_redirects=True,
        )
        self.client.post(
            "/login",
            data={"email": "pdfuser@example.com", "password": "secret123"},
            follow_redirects=True,
        )

        self.client.post(
            "/calculate",
            json={
                "patient_name": "Jane Doe",
                "patient_id": "P-100",
                "age": 40,
                "sex": "Female",
                "xray_type": "PA",
                "kvp": 110,
                "mas": 2,
                "fsd": 150,
                "machine_output": 0.027,
                "bsf": 1.2,
            },
            follow_redirects=True,
        )

    def test_pdf_report_route_returns_pdf(self):
        response = self.client.get("/report.pdf?id=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/pdf", response.content_type)
        self.assertGreater(len(response.data), 100)


if __name__ == "__main__":
    unittest.main()
