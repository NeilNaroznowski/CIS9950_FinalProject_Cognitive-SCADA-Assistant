import json
from neo4j import GraphDatabase

# Neo4j connection credentials
URI = "neo4j://127.0.0.1:7687"
USER = "neo4j"
PASSWORD = "password" # Update to match your local instance

def parse_haystack_json(filepath):
    """Parses the Project Haystack JSON and extracts all nodes and edges."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    raw_nodes = []
    raw_edges = []
    
    for row in data.get('rows', []):
        node_id = row.get('id', {}).get('val')
        if not node_id:
            continue
            
        properties = {}
        refs = {}
        
        for key, value in row.items():
            if key == 'id': continue
            
            if isinstance(value, dict):
                kind = value.get('_kind')
                if kind == 'ref':
                    refs[key] = value.get('val')
                elif kind == 'marker':
                    properties[key] = True 
                elif kind == 'number':
                    properties[key] = value.get('val')
                else:
                    properties[key] = str(value)
            else:
                properties[key] = value
                
        # Determine primary node label
        label = "Entity"
        if properties.get('site'): label = "Site"
        elif properties.get('equip'): label = "Equip"
        elif properties.get('point'): label = "Point"
        elif properties.get('space'): label = "Space"
        elif properties.get('weather'): label = "Weather"
        
        raw_nodes.append({
            "id": node_id,
            "label": label,
            "dis": properties.get('dis', node_id),
            "refs": refs,
            "properties": properties
        })
        
        # Build edges from reference tags
        for ref_type, target_id in refs.items():
            raw_edges.append({
                "source": node_id,
                "target": target_id,
                "type": ref_type.upper()
            })
            
    return raw_nodes, raw_edges

def ingest_to_neo4j(uri, user, password, nodes, edges):
    """Writes all extracted nodes and edges to the Neo4j database."""
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def create_graph(tx):
        # Clear existing data to ensure a clean run
        tx.run("MATCH (n) DETACH DELETE n")
        
        # Insert Nodes
        for node in nodes:
            # We store the Haystack 'id' and 'dis' (display name)
            query = (
                f"CREATE (n:{node['label']} {{id: $id, name: $name}})"
            )
            tx.run(query, id=node['id'], name=node['dis'])
            
        # Insert Edges
        for edge in edges:
            query = (
                f"MATCH (source {{id: $source_id}}) "
                f"MATCH (target {{id: $target_id}}) "
                f"MERGE (source)-[:{edge['type']}]->(target)"
            )
            tx.run(query, source_id=edge['source'], target_id=edge['target'])
            
    with driver.session() as session:
        session.execute_write(create_graph)
        
    driver.close()
    print(f"Ingestion complete: {len(nodes)} nodes and {len(edges)} edges loaded.")

if __name__ == "__main__":
    # 1. Parse the entire Bravo site
    all_nodes, all_edges = parse_haystack_json('bravo.json')
    
    # 2. Push everything to Neo4j
    ingest_to_neo4j(URI, USER, PASSWORD, all_nodes, all_edges)