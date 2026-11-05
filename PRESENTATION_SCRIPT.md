# Presentation Script – Local RAG Chat

**Total time: about 8–9 minutes** (+ Q&A)

| Part | Time | Total |
|---|---|---|
| Slide 1 – Local RAG Chat | 0:45 | 0:45 |
| Slide 2 – How RAG works | 1:30 | 2:15 |
| Slide 3 – Tech stack and features | 1:00 | 3:15 |
| Transition + Live demo | 4:30 | 7:45 |
| Slide 4 – Demo and takeaways + closing | 1:00 | 8:45 |

> Tip: Speak slowly. Short pauses after each sentence are fine. Reading is OK.

---

## 1. Checklist BEFORE the presentation (15 minutes before)

- [ ] **Start Ollama:** open the Ollama app, or run `ollama serve` in a terminal.
- [ ] **Check the models:** `ollama list` → `llama3.2` and `nomic-embed-text` must be there.
- [ ] **Start the app:**
      `cd local-rag-chat` → `source .venv/bin/activate` → `streamlit run app.py`
- [ ] **Browser:** open `http://localhost:8501`. Zoom to 125% so people can read it.
- [ ] **Prepare the knowledge base:** click **🗑️ Clear knowledge base**, so the demo starts empty.
- [ ] **Warm up the model:** index the sample folder once, ask one test question, then click
      **Clear knowledge base** again. (The first answer is slower because the model loads into memory.)
- [ ] **Have the PDF ready:** open Finder at `local-rag-chat/data/documents/sample/` (for drag and drop of `travel_policy.pdf`).
- [ ] **VS Code:** open the project, collapse all folders, then open `src/` with `backend/` and `frontend/` visible.
- [ ] **Close other apps** (free RAM, no notifications). Turn on "Do not disturb".
- [ ] **Optional:** turn off Wi-Fi to prove it works offline.
- [ ] **Share screen:** share the whole screen (browser + VS Code), not only one window.

---

## 2. Slides

### Slide 1 – "Local RAG Chat" (≈ 45 seconds)

> Hello everyone. Today I want to show you my project: **Local RAG Chat**.
>
> The idea is simple. You can ask questions about your own files – for example PDFs, Word
> files or notes – and you get an answer in a chat.
>
> I built it with three tools: **Streamlit** for the interface, **Ollama** with the model
> **llama3.2**, and **ChromaDB** as the database.
>
> The most important point: it runs **100% offline**. No cloud, no API key. My documents never
> leave my computer.

### Slide 2 – "How RAG works" (≈ 1 minute 30 seconds)

> How does it work? RAG means **Retrieval-Augmented Generation**. There are two phases.
>
> **Phase one is indexing.** This happens only once per file.
> First, we **load** the file and read the text.
> Then we **split** the text into small pieces. We call them chunks. Each chunk has about
> 1000 characters. Two chunks share 200 characters, so we do not lose information at the border.
> Next, we **embed** every chunk with the model **nomic-embed-text**. An embedding is a list of
> numbers that describes the meaning of the text.
> Finally, we **store** these vectors in **ChromaDB**.
>
> **Phase two is answering.** This happens for every question.
> The user **asks** a question.
> We turn the question into a vector too, and we **retrieve** the top-k most similar chunks.
> Then **llama3.2 generates** the answer. And here is the important rule: it may use **only this
> context**, not its own knowledge.
> At the end, the answer **cites** the sources with numbers, like [1] and [2].
>
> So the model does not need to know my documents. It only needs to read the right parts.

### Slide 3 – "Tech stack and features" (≈ 1 minute)

> Here is the tech stack.
> The interface is **Streamlit**. The language model is **llama3.2**, running in **Ollama**.
> For embeddings I use **nomic-embed-text**. The vector database is **ChromaDB**.
> And to read files, I use **pypdf** for PDFs and **python-docx** for Word files.
>
> And these are the features:
> - You can **upload files** in the browser, or **scan a whole folder** on your computer.
> - Files that are **already indexed are skipped**. I check this with a hash of the file content.
> - You can **pick any local model** that is installed in Ollama.
> - You can **adjust k** – that means how many chunks the model gets.
> - Every answer **cites the file and the page**.
> - There is a **short chat memory**, so follow-up questions work.
> - And there is a **one-click reset** for the knowledge base.
>
> Now let me show you the app live.

---

## 3. Transition to the live demo (≈ 10 seconds)

> Enough slides. Let's see it in action. I switch to my browser now.

**DO:** Switch to the browser with `localhost:8501`.

---

## 4. LIVE DEMO (≈ 4 minutes 30 seconds)

### Step 1 – Show the app on localhost
**DO:** Point at the address bar.
**SAY:**
> As you can see, the app runs on **localhost, port 8501**. On the left is the sidebar with my
> documents. In the middle is the chat. The knowledge base is empty right now: zero chunks.

### Step 2 – Upload a PDF
**DO:** Drag `travel_policy.pdf` into the **Upload** box. Click **Index uploads**.
**SAY:**
> First, I upload a PDF. It is a travel policy of a fictional company, Northwind Labs. It has two
> pages. I click "Index uploads"…
> Done: **1 new file**. The status says it created a few chunks.

### Step 3 – Scan a folder from my computer
**DO:** In **Folder path**, type `data/documents/sample`. Click **Scan & index folder**.
**SAY:**
> Now I index a whole folder from my computer. This folder has a company handbook, a product
> FAQ, an IT security policy – and the same travel PDF again.
> Look at the result: **3 new, 1 already indexed**. The PDF was skipped, because the app knows
> the file content already. So nothing is indexed twice.

**DO:** Point at the status "N chunks from M file(s)" and the file list.

### Step 4 – Ask questions
**DO:** Type: `How many vacation days do employees get?`
**SAY:**
> Let's ask a question. "How many vacation days do employees get?"
> The answer comes in word by word – this is streaming from the local model.

**Expected answer:** *28 vacation days per year; after 5 years, 2 extra days (30 in total).* [n]

**DO:** Open **📎 Sources**.
**SAY:**
> If I open "Sources", I can see where the answer comes from: the file name, the similarity
> score, and the text itself. So I can check that the model did not invent anything.
> Below the answer you see the model and the response time.

**DO:** Type: `What is the hotel budget in London?`
**SAY:**
> Now a question about the PDF.

**Expected answer:** *220 EUR per night.* Source: `travel_policy.pdf – page 2`.
**SAY:**
> And here we even get the **page number**: page 2 of the PDF.

**DO:** Type: `How much does the Nimbus starter kit cost and how long do the batteries last?`
**Expected answer:** *129 EUR; the batteries last about 2 years.* Source: `product_faq.md`.
**SAY:**
> This question needs two facts from the product FAQ. It finds both.

**DO (optional, if time):** Type: `And how many days can I work from home?`
**Expected answer:** *Up to 3 days per week* (Tuesday is team day in the office).

### Step 5 – Grounding: a question that is NOT in the documents
**DO:** Type: `What is the capital of France?`
**SAY:**
> Now a test. "What is the capital of France?" The model knows the answer, of course. But it is
> not in my documents.

**Expected answer:** *I couldn't find that in your documents.*
**SAY:**
> And this is exactly what I want. The model says: **"I couldn't find that in your documents."**
> It does not use its own knowledge. This is called **grounding**, and it reduces
> hallucinations.

*(Alternative question: `Who is the CEO of Northwind Labs?` → same answer.)*

### Step 6 – Tab "How it works"
**DO:** Click the tab **ℹ️ How it works**.
**SAY:**
> In this tab, the app explains the two phases – the same as on my slide. And here you see
> the current settings: the models, chunk size 1000, overlap 200, k, the number of chunks, and
> the path of the database on my disk.

### Step 7 – Code structure in VS Code
**DO:** Switch to VS Code. Show `src/frontend` and `src/backend`.
**SAY:**
> Finally, a quick look at the code. The project has a clear structure.
> **frontend** is only the Streamlit interface.
> **backend** has all the logic: loaders, chunker, services, and adapters for Ollama and ChromaDB.
> The frontend only talks to one file: **api.py**. This is the public interface of the backend.
> The backend does not know Streamlit at all.

**DO:** Open `src/backend/ports.py` for 5 seconds.
**SAY:**
> Here are the interfaces. Because of them, I can test everything **without Ollama**, with fake
> components. I have 46 tests, and they run in less than one second.

**DO:** Switch back to the slides.

---

## 5. Slide 4 – "Demo and takeaways" + closing (≈ 1 minute)

> To run it yourself, you need only **four commands**:
> `ollama pull llama3.2`, `ollama pull nomic-embed-text`, `pip install -r requirements.txt`,
> and `streamlit run app.py`.
>
> My takeaways:
> **Private** – everything stays on my computer.
> **Grounded** – answers come only from my documents, with sources.
>
> But there are also **limits**. Small models are **slower** on a laptop and sometimes less
> precise. And **scanned PDFs** have no text, so they would need **OCR**.
>
> **Next steps** would be: OCR for scanned files, **hybrid search** – that means keyword search
> plus vector search – and **re-ranking** to sort the best chunks to the top.
>
> Thank you for listening! I'm happy to answer your questions.

---

## 6. Q&A preparation

**1. Why RAG instead of fine-tuning?**
> Fine-tuning changes the model weights. It is expensive, it needs a GPU, and you must do it
> again every time a document changes. With RAG, I just add a file and it is available
> immediately. Also, RAG can show the sources. Fine-tuning cannot.

**2. Why Ollama?**
> Ollama makes it very easy to run open-source models locally. One command to download a
> model, and it has a simple Python client. It's free, private, and works offline.

**3. What is an embedding?**
> An embedding is a list of numbers – here 768 numbers – that represents the meaning of a text.
> Texts with a similar meaning get similar numbers. So we can search by meaning, not only by
> exact words.

**4. Why chunk overlap?**
> Sometimes an important fact is split between two chunks. The overlap repeats the last
> sentences of one chunk at the start of the next one. So the full context is in at least one chunk.

**5. What happens if the answer is not in the documents?**
> The system prompt tells the model to use only the context. If the answer is not there, it must
> say "I couldn't find that in your documents." I showed this in the demo with the capital of France.

**6. Why ChromaDB?**
> ChromaDB runs inside my Python app, no extra server. It saves the data on disk, and it can store
> metadata like file name, page and file hash. I need the hash to skip duplicates and to delete old
> versions of a file. FAISS is faster, but it only stores vectors.

**7. How is the frontend separated from the backend?**
> They are two separate packages. The frontend imports only one file, `api.py`. This is a facade
> with a few methods, like `index_folder` and `ask`. The backend does not import Streamlit.
> Inside the backend, I use ports and adapters: the logic only knows interfaces, and Ollama and
> ChromaDB are plugged in as adapters.

**8. How would you scale it?**
> First, I would put the backend behind **FastAPI**. Because of the facade, every method becomes
> an endpoint. Then I would use a vector database server like Qdrant or pgvector, run it with
> Docker, and use a GPU server for bigger models.

**9. What are the limits?**
> Small models are slower and sometimes forget a citation. Scanned PDFs need OCR. Pure vector
> search can miss exact keywords. And questions in another language than the documents work less
> well.

**10. How did you test it?**
> I have 46 unit tests with pytest. They use fake components, so they run without Ollama in under
> one second. I test the chunker, the loaders, the duplicate check, the prompt and the API.
> I also tested the full app with the real model, and I use ruff for code quality.

**Bonus – Why did you not use LangChain?**
> I wanted to understand every step. My own code is short, easy to explain, and has fewer
> dependencies.

**Bonus – Why is k = 4?**
> Four chunks give enough context but not too much noise for a small model. You can change it with
> the slider.

---

## 7. Backup plan – if the demo has problems

| Problem | What I do | What I say |
|---|---|---|
| Red box "Start Ollama with: ollama serve" | Open terminal, run `ollama serve`, reload the page | "Ollama is not running yet – you see that the app tells me exactly what to do. One second." |
| Yellow box "Run: ollama pull …" | Run the command shown | "A model is missing – the app checks this at the start." |
| The first answer is very slow | Wait, keep talking | "The first question is slower because the model loads into memory. The next ones are faster." |
| Answer without a citation number | Open the Sources | "Small models sometimes forget the number, but the sources are always shown here." |
| Wrong or incomplete answer | Increase k to 6 and ask again | "Let me give the model more context with the k slider." |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` | "Another app is using the port, I just use the next one." |
| Folder not found | Type `data/documents/sample` exactly | "The path is relative to the project folder." |
| Browser/app freezes | Ctrl+C in terminal, `streamlit run app.py` again | "Let me restart it – the data is saved on disk, so nothing is lost." |
| Everything fails | Show screenshots / the code in VS Code, explain the flow | "The live demo does not want to work today, so let me show you the code and walk you through what happens." |

---

## 8. Small glossary

| Term | Simple explanation |
|---|---|
| **RAG** | Retrieval-Augmented Generation. First find the right text parts, then let the model answer with them. |
| **LLM** | Large Language Model. A model that can read and write text, like llama3.2. |
| **Embedding** | A list of numbers that describes the meaning of a text. |
| **Vector** | A list of numbers. Here: 768 numbers for each chunk. You can think of it as a point in space. |
| **Chunk** | A small piece of a document, here up to about 1000 characters. |
| **Top-k** | The k most similar chunks to the question (for example the best 4). |
| **Cosine similarity** | Measures how similar two vectors are by their direction. 1 means very similar, 0 means not related. |
| **Grounding** | The model must base its answer on the given context, not on its own knowledge. |
| **Ollama** | A tool to download and run open-source LLMs on your own computer. |
| **Vector database** | A database that stores vectors and finds the most similar ones quickly (here ChromaDB). |
