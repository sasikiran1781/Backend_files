from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from datetime import datetime
import os
import json

class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor("#008B8B"), # Cyan/Teal
            spaceAfter=12
        )
        self.subheader_style = ParagraphStyle(
            'SubHeaderStyle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#333333"),
            spaceBefore=10,
            spaceAfter=10,
            borderPadding=5,
            borderWidth=0,
            leftIndent=0
        )
        self.normal_style = self.styles['Normal']
        self.bold_style = ParagraphStyle(
            'BoldStyle',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold'
        )

    def generate_report_pdf(self, report_data, output_path):
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        elements = []

        # Header: App Name and Report Title
        elements.append(Paragraph("REVA - AI Medical Analysis", self.header_style))
        elements.append(Paragraph(f"Medical Report: {report_data.get('report_type', 'General')}", self.subheader_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Patient Info Section
        p_identity = report_data.get('patient_identity', {})
        patient_info = [
            [Paragraph("<b>Patient Name:</b>", self.normal_style), p_identity.get('patient_name', 'N/A')],
            [Paragraph("<b>Patient ID:</b>", self.normal_style), p_identity.get('id', 'N/A')],
            [Paragraph("<b>Age/Gender:</b>", self.normal_style), f"{p_identity.get('age', 'N/A')} / {p_identity.get('gender', 'N/A')}"],
            [Paragraph("<b>Hospital:</b>", self.normal_style), p_identity.get('hospital_name', 'N/A')],
            [Paragraph("<b>Report Date:</b>", self.normal_style), p_identity.get('report_date', 'N/A')]
        ]
        
        t_patient = Table(patient_info, colWidths=[1.5 * inch, 4 * inch])
        t_patient.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_patient)
        elements.append(Spacer(1, 0.3 * inch))

        # Recovery Score & Severity
        score = report_data.get('recovery_score', 'N/A')
        severity = report_data.get('risk_analysis', {}).get('severity_level', 'Stable')
        
        score_data = [
            [Paragraph("<b>Recovery Score:</b>", self.normal_style), f"{score}/100"],
            [Paragraph("<b>Health Status:</b>", self.normal_style), severity]
        ]
        t_score = Table(score_data, colWidths=[1.5 * inch, 4 * inch])
        t_score.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.whitesmoke),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.green if str(score).isdigit() and int(score) > 70 else colors.orange),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(Paragraph("Recovery Summary", self.subheader_style))
        elements.append(t_score)
        elements.append(Spacer(1, 0.2 * inch))

        # Medical Metrics
        metrics = report_data.get('medical_metrics', {})
        if metrics:
            elements.append(Paragraph("Medical Metrics", self.subheader_style))
            metric_rows = [["Metric", "Value", "Unit"]]
            for name, detail in metrics.items():
                if isinstance(detail, dict):
                    metric_rows.append([
                        name.replace('_', ' ').title(),
                        detail.get('value', 'N/A'),
                        detail.get('unit', '')
                    ])
            
            t_metrics = Table(metric_rows, colWidths=[2 * inch, 2 * inch, 1.5 * inch])
            t_metrics.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#008B8B")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            elements.append(t_metrics)
            elements.append(Spacer(1, 0.3 * inch))

        # Diagnosis & Risks
        elements.append(Paragraph("Analysis & Diagnosis", self.subheader_style))
        diagnosis = report_data.get('diagnosis', 'No detailed diagnosis available.')
        elements.append(Paragraph(diagnosis, self.normal_style))
        elements.append(Spacer(1, 0.1 * inch))
        
        risk_summary = report_data.get('risk_analysis', {}).get('summary', '')
        if risk_summary and risk_summary != diagnosis:
             elements.append(Paragraph(f"<b>Risk Summary:</b> {risk_summary}", self.normal_style))

        # Recommendations
        recs = report_data.get('recommendations', {})
        if recs:
            elements.append(Paragraph("Personalized Recommendations", self.subheader_style))
            
            recs_data = []
            if recs.get('foods_to_eat'):
                recs_data.append([Paragraph("<b>Foods to Eat:</b>", self.normal_style), ", ".join(recs.get('foods_to_eat'))])
            if recs.get('foods_to_avoid'):
                recs_data.append([Paragraph("<b>Foods to Avoid:</b>", self.normal_style), ", ".join(recs.get('foods_to_avoid'))])
            if recs.get('water_intake'):
                recs_data.append([Paragraph("<b>Water Intake:</b>", self.normal_style), recs.get('water_intake')])
            if recs.get('exercise'):
                recs_data.append([Paragraph("<b>Exercise:</b>", self.normal_style), recs.get('exercise')])
            if recs.get('recovery_precautions'):
                recs_data.append([Paragraph("<b>Precautions:</b>", self.normal_style), ", ".join(recs.get('recovery_precautions'))])

            if recs_data:
                t_recs = Table(recs_data, colWidths=[1.5 * inch, 4 * inch])
                t_recs.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(t_recs)

        # Medications Section
        medications = report_data.get('medications', [])
        if medications:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Prescribed Medications", self.subheader_style))
            
            med_rows = [["Medication", "Dosage", "Frequency", "Duration"]]
            for med in medications:
                if isinstance(med, dict):
                    med_rows.append([
                        med.get('name', 'N/A'),
                        med.get('dosage', 'N/A'),
                        med.get('frequency', 'N/A'),
                        med.get('duration', 'N/A')
                    ])
            
            t_meds = Table(med_rows, colWidths=[2 * inch, 1.2 * inch, 1.2 * inch, 1.1 * inch])
            t_meds.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4682B4")), # Steel Blue
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elements.append(t_meds)

        # Follow-up Section
        follow_up = report_data.get('follow_up_analysis', {})
        if follow_up and follow_up.get('is_follow_up'):
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph("Follow-up Comparison", self.subheader_style))
            
            trend = follow_up.get('health_trend', 'Stable')
            improvement = follow_up.get('improvement_percentage', 0)
            
            f_data = [
                [Paragraph("<b>Health Trend:</b>", self.normal_style), trend],
                [Paragraph("<b>Improvement:</b>", self.normal_style), f"{improvement}%"]
            ]
            t_follow = Table(f_data, colWidths=[1.5 * inch, 4 * inch])
            t_follow.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(t_follow)

        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"Generated by REVA AI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        elements.append(Paragraph("Disclaimer: This is an AI-generated summary. Please consult your doctor for medical advice.", self.normal_style))

        # Build PDF
        doc.build(elements)
        return output_path
