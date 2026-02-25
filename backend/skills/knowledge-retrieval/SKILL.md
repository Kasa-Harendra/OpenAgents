---
name: knowledge-retrieval
description: RAG-based document search and answer generation with source citations from local vector store using semantic similarity
license: MIT
compatibility: Requires indexed vector store with embeddings
metadata:
  author: OpenAgents
  version: "1.0"
  allowed-tools: query_vectorstore, create_index, list_indexed_documents
---

# knowledge-retrieval

## Overview

This skill provides comprehensive guidance for Retrieval-Augmented Generation (RAG) operations. Use this to search through indexed local documents and provide accurate, sourced answers based exclusively on retrieved context.

## Core Principles

1. **Only Retrieved Context**: Answer EXCLUSIVELY from retrieved documents
2. **Always Cite Sources**: Include source document names
3. **No Hallucination**: Never add external knowledge or guesses
4. **Concise Answers**: Keep responses brief (3-4 sentences max)
5. **Explicit "Unknown"**: Clearly state when information isn't found

## Instructions

### Step 1: Understand the User's Question

Parse the user's query to extract:

- **Main topic**: What are they asking about?
- **Specific details**: What exact information do they need?
- **Context from history**: Is this a follow-up question?
- **Search terms**: Key words for retrieval

**Example Parsing**:

- Question: "How do I configure the database connection?"
- Topic: Database configuration
- Search terms: "database", "configuration", "connection"

---

### Step 2: Retrieve Relevant Documents

Query the vector store to find relevant context:

```json
{
  "tool": "query_vectorstore",
  "params": {
    "query": "database configuration connection",
    "top_k": 4,
    "directory": "./docs"
  }
}
```

**Retrieval Strategy**:

- **top_k = 3-5**: Retrieve 3-5 most relevant chunks
- **Balance**: Too few chunks = might miss answer; too many = noise
- **Relevance threshold**: Filter chunks below 0.5 similarity score

**Retrieved Context Structure**:

```python
{
  "chunks": [
    {
      "content": "Database connection string format: postgresql://user:pass@host:port/db",
      "source": "database-setup.md",
      "score": 0.89
    },
    {
      "content": "Configure in .env file with DB_HOST and DB_PORT variables",
      "source": "configuration-guide.md",
      "score": 0.76
    }
  ]
}
```

---

### Step 3: Assess Retrieved Context Relevance

Evaluate if retrieved chunks contain the answer:

#### High Relevance (Score > 0.7)

- ✅ Chunks directly relate to question
- ✅ Contains specific information requested
- **Action**: Proceed to answer generation

#### Medium Relevance (Score 0.5-0.7)

- ⚠️ Chunks somewhat related but not exact
- **Action**: Use cautiously, note uncertainty

#### Low Relevance (Score < 0.5)

- ❌ Chunks don't address the question
- **Action**: Report "information not found"

---

### Step 4: Generate Answer from Context

Synthesize answer based ONLY on retrieved content:

#### Answer Guidelines

1. **Use ONLY retrieved information** - No external knowledge
2. **Quote or paraphrase** from retrieved chunks
3. **Keep concise** - 3-4 sentences maximum
4. **Direct answer first** - Then supporting details
5. **Maintain accuracy** - Don't embellish or interpret

#### Answer Templates

**When Information Found**:

```
Based on the documentation: [Direct answer from retrieved context]

[Supporting detail 1 from context]
[Supporting detail 2 from context]

Source: [filename1], [filename2]
```

**When Information Partially Found**:

```
Based on available documentation: [Partial answer]

Note: The indexed documents contain limited information on [missing aspect].

Source: [filename]
```

**When Information NOT Found**:

```
I couldn't find information about [specific topic] in the indexed documents.

The available documents cover [related topics found], but don't address [specific question].

Suggestions:
- Check if relevant documentation is indexed
- Rephrase the question
- Index additional documentation
```

---

### Step 5: Cite Sources

Always include source citations:

**Citation Format**:

```
Source: database-setup.md, configuration-guide.md
```

**Multiple Chunks from Same File**:

```
Source: user-manual.md (sections: Setup, Configuration)
```

**With Confidence Level** (optional):

```
Source: api-documentation.md
Confidence: High (similarity score: 0.89)
```

---

## RAG Workflow Examples

### Example 1: Straightforward Query

**Question**: "What ports does the application use?"

**Retrieval**:

```json
{
  "query": "application ports network",
  "top_k": 3
}
```

**Retrieved Context**:

```
Chunk 1 (0.92): "The application listens on port 8000 for HTTP and port 8443 for HTTPS."
Source: deployment-guide.md

Chunk 2 (0.78): "Configure ports in config.yaml under server.http_port and server.https_port"
Source: configuration-reference.md
```

**Answer**:

```
Based on the documentation: The application uses port 8000 for HTTP and port 8443 for HTTPS.

These ports can be configured in the config.yaml file under server.http_port and server.https_port settings.

Source: deployment-guide.md, configuration-reference.md
```

---

### Example 2: Follow-up Question

**Question**: "How do I change the default port?"

**Context from History**: Previous question was about ports

**Retrieval** (with history context):

```json
{
  "query": "change configure port settings config",
  "top_k": 3
}
```

**Answer**:

```
Based on the documentation: Edit the config.yaml file and update the server.http_port value to your desired port number. After changing the port, restart the application for changes to take effect.

Source: configuration-reference.md
```

---

### Example 3: Information Not Found

**Question**: "What is the quantum encryption algorithm used?"

**Retrieval**:

```json
{
  "query": "quantum encryption algorithm security",
  "top_k": 4
}
```

**Retrieved Context**:

```
Chunk 1 (0.45): "The application uses SSL/TLS for secure connections."
Chunk 2 (0.38): "Authentication is handled via OAuth 2.0."
(Low relevance scores)
```

**Answer**:

```
I couldn't find information about quantum encryption algorithms in the indexed documents.

The available documentation covers standard security measures (SSL/TLS, OAuth 2.0) but doesn't mention quantum encryption specifically.

Suggestions:
- Verify if this feature exists in the application
- Check if relevant security documentation is indexed
- Consult external documentation or developers
```

---

## Context Management Strategies

### Handling Chat History

**First Question in Conversation**:

- Use query as-is
- No additional context needed

**Follow-up Questions**:

- Combine current question with previous topic
- Example:
  - Q1: "How to install the app?"
  - Q2: "What about dependencies?"
  - Combined query: "install app dependencies requirements"

### Reformulating Queries

If first retrieval yields poor results:

**Strategy 1: Expand Search Terms**

```python
Original: "API authentication"
Expanded: "API authentication security tokens OAuth login"
```

**Strategy 2: Simplify Query**

```python
Original: "How do I configure the PostgreSQL database connection pool settings?"
Simplified: "database connection configuration"
```

**Strategy 3: Use Synonyms**

```python
Original: "terminate process"
Alternative: "stop process kill shutdown"
```

---

## Anti-Hallucination Rules

❌ **Never Do This**:

```
Question: "What is the company's revenue?"
Retrieved: No relevant information found
Bad Answer: "Based on industry standards, the company likely has revenue of $XX million..."
```

✅ **Always Do This**:

```
Question: "What is the company's revenue?"
Retrieved: No relevant information found
Good Answer: "I couldn't find revenue information in the indexed documents."
```

---

## Confidence Levels

Optionally rate answer confidence:

**High Confidence**:

- Multiple relevant chunks (score > 0.8)
- Consistent information across sources
- Direct match to question

**Medium Confidence**:

- Some relevant chunks (score 0.5-0.8)
- Partial information available
- Indirect match to question

**Low Confidence**:

- Few relevant chunks (score < 0.5)
- Limited information
- Note: State uncertainty explicitly

---

## Error Handling

### Error 1: Vector Store Not Initialized

**Response**:

```
❌ Knowledge base not initialized

The vector store has not been created or indexed yet.

Suggested Fix:
1. Index documents using create_index tool
2. Specify the directory containing documents to index
3. Wait for indexing to complete
4. Retry the query

Example: create_index(directory="./docs")
```

---

### Error 2: No Documents Indexed

**Response**:

```
❌ No documents found in knowledge base

The vector store exists but contains no indexed documents.

Suggested Fix:
1. Add documents to the target directory
2. Re-run indexing process
3. Verify document formats are supported (txt, md, pdf, docx)

Supported formats: .txt, .md, .pdf, .docx
```

---

### Error 3: Retrieval Timeout

**Response**:

```
❌ Query timeout

The vector store query took too long to complete.

Possible causes:
- Very large knowledge base
- Complex query
- System resource constraints

Suggested Fix:
- Simplify the query
- Reduce top_k parameter
- Check system resources
```

---

## Best Practices

1. **Retrieve 3-5 chunks**: Balance between coverage and noise
2. **Check relevance scores**: Filter out low-scoring chunks
3. **Always cite sources**: Build user trust
4. **Be concise**: 3-4 sentences maximum
5. **Admit unknowns**: Better than guessing
6. **Use context history**: For better follow-up answers
7. **Reformulate if needed**: Try different search terms

---

## Advanced Example: Multi-Document Synthesis

**Question**: "What are all the authentication methods supported?"

**Retrieval**:

```
Chunk 1 (0.88): "OAuth 2.0 authentication supported via Google and GitHub providers"
Source: auth-setup.md

Chunk 2 (0.85): "API key authentication available for service-to-service calls"
Source: api-documentation.md

Chunk 3 (0.79): "SAML SSO integration for enterprise customers"
Source: enterprise-features.md

Chunk 4 (0.71): "Basic username/password authentication for development environments"
Source: development-guide.md
```

**Answer**:

```
Based on the documentation, the application supports four authentication methods:

1. OAuth 2.0 (Google and GitHub providers)
2. API key authentication for service-to-service calls
3. SAML SSO integration for enterprise customers
4. Basic username/password authentication for development environments

Sources: auth-setup.md, api-documentation.md, enterprise-features.md, development-guide.md
```

---

## Troubleshooting

**Q: Getting irrelevant results**
**A**: Reformulate query with more specific terms, adjust top_k, check if relevant docs are indexed

**Q: Answer too verbose**
**A**: Limit to 3-4 sentences, focus on direct answer first

**Q: Missing information from docs I know exist**
**A**: Check if docs are indexed, verify file format support, re-index if needed

**Q: Contradictory information from different sources**
**A**: Present both perspectives, note the discrepancy, cite both sources
