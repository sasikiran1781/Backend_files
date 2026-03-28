from database.models import HealthReport, FollowupComparison, db
import json

class RecoveryService:
    @staticmethod
    def get_latest_metrics(patient_id):
        """
        Gets metrics from the most recent report of a patient.
        """
        latest = HealthReport.query.filter_by(patient_id=patient_id).order_by(HealthReport.created_at.desc()).first()
        if latest and latest.medical_metrics_json:
            # If the column is db.JSON, SQLAlchemy already returns it as a dict.
            # No need to call json.loads().
            if isinstance(latest.medical_metrics_json, str):
                try:
                    return json.loads(latest.medical_metrics_json)
                except:
                    return {}
            return latest.medical_metrics_json
        return None

    @staticmethod
    def store_comparison(patient_id, prev_report_id, curr_report_id, comparison_data):
        """
        Stores the follow-up improvement data.
        """
        comp = FollowupComparison(
            patient_id=patient_id,
            previous_report_id=prev_report_id,
            current_report_id=curr_report_id,
            improvement_percentage=comparison_data.get('improvement_percentage', 0.0),
            activity_improvement=comparison_data.get('activity_improvement', 0.0),
            wellness_improvement=comparison_data.get('wellness_improvement', 0.0),
            decline_percentage=comparison_data.get('decline_percentage', 0.0),
            health_trend=comparison_data.get('health_trend', 'Stable'),
            comparison_summary=comparison_data.get('health_trend_summary') or comparison_data.get('comparison_summary'),
            comparisons_json=comparison_data.get('comparisons', {})
        )
        db.session.add(comp)
        db.session.commit()
        return comp
                    