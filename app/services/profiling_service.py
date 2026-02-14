from sqlalchemy import text
from app.domain.models import ColumnModel, ColumnProfile


class ProfilingService:

    def __init__(self, engine, session):
        self.engine = engine
        self.session = session

    def profile_column(self, table_name, column_name, data_type):
        with self.engine.connect() as conn:

            total_query = f"SELECT COUNT(*) FROM {table_name};"
            total_rows = conn.execute(text(total_query)).scalar()

            if total_rows == 0:
                return None

            null_query = f"""
            SELECT COUNT(*) FROM {table_name}
            WHERE {column_name} IS NULL;
            """
            null_count = conn.execute(text(null_query)).scalar()

            distinct_query = f"""
            SELECT COUNT(DISTINCT {column_name})
            FROM {table_name};
            """
            distinct_count = conn.execute(text(distinct_query)).scalar()

            min_value = None
            max_value = None
            mean_value = None

            if data_type not in ["boolean", "USER-DEFINED"]:
                min_query = f"SELECT MIN({column_name}) FROM {table_name};"
                max_query = f"SELECT MAX({column_name}) FROM {table_name};"

                min_value = conn.execute(text(min_query)).scalar()
                max_value = conn.execute(text(max_query)).scalar()

            if data_type in ["integer", "double precision", "numeric"]:
                mean_query = f"SELECT AVG({column_name}) FROM {table_name};"
                mean_value = conn.execute(text(mean_query)).scalar()

            null_percentage = (null_count / total_rows) * 100

            return {
                "null_percentage": null_percentage,
                "distinct_count": distinct_count,
                "min_value": str(min_value) if min_value is not None else None,
                "max_value": str(max_value) if max_value is not None else None,
                "mean": mean_value
            }

    def run_profiling(self):
        columns = self.session.query(ColumnModel).all()

        for column in columns:
            table_name = column.table.name
            column_name = column.name

            profile_data = self.profile_column(
                table_name,
                column_name,
                column.data_type
            )

            if profile_data:
                profile = ColumnProfile(
                    null_percentage=profile_data["null_percentage"],
                    distinct_count=profile_data["distinct_count"],
                    min_value=profile_data["min_value"],
                    max_value=profile_data["max_value"],
                    mean=profile_data["mean"],
                    column_id=column.id
                )

                self.session.add(profile)

        self.session.commit()
        print("Profiling completed successfully!")
