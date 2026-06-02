# Usage Examples

## Local File Search Examples

### 1 – List all PDF files

**Query:**
```
What PDF files are available in our system?
```

**Expected output:**
```json
{
  "query_type": "local_file_search",
  "filters": {
    "file_name_contains": null,
    "extension": ".pdf",
    ...
  },
  "results": [
    {
      "file_name": "amphibian_lifecycle_notes.pdf",
      "folder_path": "data/sample_files/zoology",
      "file_extension": ".pdf",
      "created_date": "2026-06-01T10:15:00",
      "modified_date": "2026-06-01T10:15:00",
      "file_size_bytes": 512
    },
    {
      "file_name": "forest_biodiversity_inventory.pdf",
      "folder_path": "data/sample_files/ecology",
      "file_extension": ".pdf",
      "created_date": "2026-06-01T10:15:00",
      "modified_date": "2026-06-01T10:15:00",
      "file_size_bytes": 512
    }
  ],
  "result_count": 2,
  "errors": []
}
```

---

### 2 – List all files in zoology folder

**Query:**
```
Show files in the zoology folder
```

**Expected output:** JSON with results whose `folder_path` contains `zoology`.

---

### 3 – List all DOCX files

**Query:**
```
List all docx files
```

**Expected output:** JSON list containing only `.docx` files.

---

### 4 – List all text files

**Query:**
```
Find txt files in our local system
```

**Expected output:** JSON with `.txt` files only.

---

### 5 – List all files (no filter)

**Query:**
```
Show all files available in our local system
```

**Expected output:** All supported files, no extension filter applied.

---

### 6 – Files in biology directory

**Query:**
```
What files are in the biology directory?
```

**Expected output:** JSON with results from the biology folder only.

---

### 7 – Excel spreadsheet files

**Query:**
```
Find xlsx files
```

**Expected output:** JSON with `.xlsx` files only.

---

## Microsoft / Azure Examples

> **Note:** These queries require `OPENAI_API_KEY` to be set.

### 1 – Azure Blob Storage

**Query:**
```
What is Azure Blob Storage?
```

**Expected output:**
```
Azure Blob Storage is Microsoft's massively scalable and secure object storage for cloud-native workloads, archives, data lakes, high-performance computing, and machine learning. It supports hot, cool, and archive storage tiers…
```

---

### 2 – Microsoft Fabric

**Query:**
```
Explain Microsoft Fabric Lakehouse
```

**Expected output:** Concise description of the Fabric Lakehouse architecture, under 2 000 characters.

---

### 3 – Azure Entra ID

**Query:**
```
How does Azure Entra ID work?
```

**Expected output:** Brief explanation of Azure Entra ID (formerly Azure Active Directory).

---

### 4 – Azure Functions

**Query:**
```
What are Azure Functions?
```

**Expected output:** Concise explanation of serverless compute with Azure Functions.

---

### 5 – Power BI

**Query:**
```
What is Power BI used for?
```

**Expected output:** Brief description of Power BI business intelligence capabilities.

---

## Unsupported Query Examples

### 1 – Football

**Query:**
```
Who won the last football match?
```

**Expected output:**
```
Unsupported query. This agent only supports local file search and Microsoft/Azure documentation questions.
```

---

### 2 – General science

**Query:**
```
What is photosynthesis?
```

**Expected output:** Same refusal message.

---

### 3 – Cooking

**Query:**
```
How do I make pasta?
```

**Expected output:** Same refusal message.
