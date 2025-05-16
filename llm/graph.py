from langchain_neo4j import GraphCypherQAChain


def get_graphqa_cypher_chain(llm_model, graph, prompt):
    chain = GraphCypherQAChain.from_llm(
                    llm_model,
                    graph=graph,
                    verbose=True,
                    return_intermediate_steps=True,
                    allow_dangerous_requests=True,
                    cypher_prompt_template=prompt
                )
    return chain