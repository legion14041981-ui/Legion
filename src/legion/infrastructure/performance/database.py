"""Database Query Optimization - N+1 Problem Fix"""

from typing import List, Dict, Any, Optional
from collections import defaultdict


class QueryOptimizer:
    """Utilities to prevent N+1 query problems"""
    
    @staticmethod
    async def fetch_with_relations(
        db_pool,
        base_query: str,
        relation_queries: Dict[str, str],
        base_params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch base records with eager-loaded relations
        
        Example:
            results = await QueryOptimizer.fetch_with_relations(
                db_pool,
                "SELECT * FROM tasks WHERE status = $1",
                {
                    "user": "SELECT * FROM users WHERE id = ANY($1)",
                    "tags": "SELECT * FROM tags WHERE task_id = ANY($1)"
                },
                ("pending",)
            )
        """
        # Fetch base records
        base_records = await db_pool.fetch(base_query, *(base_params or ()))
        
        if not base_records:
            return []
        
        # Extract IDs for relations
        base_ids = [record['id'] for record in base_records]
        
        # Fetch all relations in parallel
        relations = {}
        for relation_name, relation_query in relation_queries.items():
            relation_records = await db_pool.fetch(relation_query, base_ids)
            
            # Group by foreign key
            grouped = defaultdict(list)
            for record in relation_records:
                fk = record.get('task_id') or record.get('id')  # Adjust based on schema
                grouped[fk].append(dict(record))
            
            relations[relation_name] = grouped
        
        # Combine results
        results = []
        for record in base_records:
            record_dict = dict(record)
            
            # Attach relations
            for relation_name, grouped_relations in relations.items():
                record_dict[relation_name] = grouped_relations.get(record['id'], [])
            
            results.append(record_dict)
        
        return results
    
    @staticmethod
    def build_batch_query(ids: List[str], table: str, id_column: str = "id") -> str:
        """
        Build efficient batch query using ANY operator
        
        Example:
            query = QueryOptimizer.build_batch_query(
                ["id1", "id2", "id3"],
                "users"
            )
            # Returns: "SELECT * FROM users WHERE id = ANY($1)"
        """
        return f"SELECT * FROM {table} WHERE {id_column} = ANY($1)"
