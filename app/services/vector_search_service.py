from sqlalchemy import text


class VectorSearchService:

    def __init__(self, engine):
        self.engine = engine

    def search(self, query_vector, top_k=10, connection_id=None):

        # Convert Python list → pgvector string format
        vector_str = "[" + ",".join(map(str, query_vector)) + "]"

        if connection_id:
            sql = """
            SELECT 
                entity_type,
                entity_id,
                vector <-> CAST(:query_vector AS vector) AS distance
            FROM embeddings
            WHERE connection_id = :connection_id
            ORDER BY vector <-> CAST(:query_vector AS vector)
            LIMIT :top_k;
            """
            params = {
                "query_vector": vector_str,
                "top_k": top_k,
                "connection_id": str(connection_id)
            }
        else:
            sql = """
            SELECT 
                entity_type,
                entity_id,
                vector <-> CAST(:query_vector AS vector) AS distance
            FROM embeddings
            ORDER BY vector <-> CAST(:query_vector AS vector)
            LIMIT :top_k;
            """
            params = {
                "query_vector": vector_str,
                "top_k": top_k
            }

        with self.engine.connect() as conn:
            result = conn.execute(
                text(sql),
                params
            )

            return result.fetchall()
