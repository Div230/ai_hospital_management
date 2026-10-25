"""Local report OCR; external clinical analysis is never automatic."""
from celery import shared_task


@shared_task(bind=True, max_retries=2, soft_time_limit=150, time_limit=180)
def analyze_medical_report_task(self, report_id):
    from patients.models import MedicalReport
    from .services.ocr import extract_text_from_file
    report = MedicalReport.objects.filter(pk=report_id).first()
    if not report or report.status == 'ANALYZED':
        return
    MedicalReport.objects.filter(pk=report_id).update(status='PROCESSING')
    try:
        text = extract_text_from_file(report.file.path)
        if not text.strip():
            raise ValueError('No readable printed text detected.')
        MedicalReport.objects.filter(pk=report_id).update(
            ocr_extracted_text=text, status='ANALYZED', ai_abnormal_values=[],
            ai_structured_summary={'summary': 'Local OCR transcription only. Review the original with a clinician.', 'parameters': []})
    except Exception as exc:
        MedicalReport.objects.filter(pk=report_id).update(status='FAILED')
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=2, soft_time_limit=150, time_limit=180)
def analyze_lab_report_task(self, lab_report_id):
    from laboratory.models import LabReport
    from .services.ocr import extract_text_from_file
    from notifications.services import notify_user
    report = LabReport.objects.select_related('test_request__patient__user').filter(pk=lab_report_id).first()
    if not report or report.is_notified:
        return
    try:
        text = extract_text_from_file(report.file.path)
        if not text.strip():
            raise ValueError('No readable printed text detected.')
        report.result_summary = text
        report.save(update_fields=['result_summary'])
        report.test_request.status = 'COMPLETED'
        report.test_request.save(update_fields=['status', 'updated_at'])
        notify_user(report.test_request.patient.user, 'LAB_REPORT_READY', 'Lab Report Available',
                    'A laboratory document is available in your portal. Consult your clinician about its contents.')
        report.is_notified = True
        report.save(update_fields=['is_notified'])
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
