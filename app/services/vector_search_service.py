from sqlalchemy import text


class VectorSearchService:

    def __init__(self, engine):
        self.engine = engine

    def search(self, query_vector, top_k=10):

        # Convert Python list → pgvector string format
        vector_str = "[" + ",".join(map(str, query_vector)) + "]"

        sql = """
        SELECT 
            entity_type,
            entity_id,
            vector <-> CAST(:query_vector AS vector) AS distance
        FROM embeddings
        ORDER BY vector <-> CAST(:query_vector AS vector)
        LIMIT :top_k;
        """

        with self.engine.connect() as conn:
            result = conn.execute(
                text(sql),
                {
                    "query_vector": vector_str,
                    "top_k": top_k
                }
            )

            return result.fetchall()
