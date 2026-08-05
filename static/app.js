const CATEGORIES = JSON.parse(document.getElementById("categories-data").textContent);

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const resultsCard = document.getElementById("resultsCard");
const resultsBody = document.getElementById("resultsBody");
const commitBtn = document.getElementById("commitBtn");
const statusEl = document.getElementById("status");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) {
    uploadFile(e.dataTransfer.files[0]);
  }
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
});

function setUploadStatus(text, cls) {
  uploadStatus.textContent = text;
  uploadStatus.className = cls || "";
}

async function uploadFile(file) {
  setUploadStatus(`Verarbeite "${file.name}" ...`, "");
  resultsCard.style.display = "none";
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) {
      setUploadStatus(data.error || "Fehler bei der Verarbeitung.", "err");
      return;
    }
    if (data.sheets_warning) {
      setUploadStatus(data.sheets_warning, "warn");
    } else {
      setUploadStatus(`${data.transactions.length} Transaktionen erkannt.`, "ok");
    }
    renderResults(data.transactions);
  } catch (err) {
    setUploadStatus("Netzwerkfehler: " + err, "err");
  }
}

function renderResults(transactions) {
  resultsBody.innerHTML = "";
  transactions.forEach((tx, idx) => {
    const tr = document.createElement("tr");
    tr.dataset.index = idx;
    if (tx.bereits_importiert) tr.classList.add("dup");

    tr.appendChild(cell(checkboxInput(!tx.bereits_importiert)));
    tr.appendChild(cell(textInput(tx.datum, "datum")));
    tr.appendChild(cell(textInput(tx.zahlungsempfaenger, "zahlungsempfaenger")));
    tr.appendChild(cell(textInput(tx.verwendungszweck, "verwendungszweck")));
    tr.appendChild(cell(numberInput(tx.betrag, "betrag")));
    tr.appendChild(cell(selectInput(tx.typ, ["Ausgabe", "Einnahme"], "typ")));
    tr.appendChild(cell(selectInput(tx.kategorie, CATEGORIES, "kategorie")));

    tr._raw = tx;
    resultsBody.appendChild(tr);
  });
  resultsCard.style.display = transactions.length ? "block" : "none";
}

function cell(el) {
  const td = document.createElement("td");
  td.appendChild(el);
  return td;
}
function checkboxInput(checked) {
  const el = document.createElement("input");
  el.type = "checkbox";
  el.checked = checked;
  el.className = "include-cb";
  return el;
}
function textInput(value, field) {
  const el = document.createElement("input");
  el.type = "text";
  el.value = value ?? "";
  el.dataset.field = field;
  return el;
}
function numberInput(value, field) {
  const el = document.createElement("input");
  el.type = "number";
  el.step = "0.01";
  el.value = value ?? "";
  el.dataset.field = field;
  return el;
}
function selectInput(value, options, field) {
  const el = document.createElement("select");
  el.dataset.field = field;
  options.forEach((opt) => {
    const o = document.createElement("option");
    o.value = opt;
    o.textContent = opt;
    if (opt === value) o.selected = true;
    el.appendChild(o);
  });
  return el;
}

commitBtn.addEventListener("click", async () => {
  const rows = Array.from(resultsBody.querySelectorAll("tr"));
  const transactions = [];
  rows.forEach((tr) => {
    const include = tr.querySelector(".include-cb").checked;
    if (!include) return;
    const tx = { ...tr._raw };
    tr.querySelectorAll("[data-field]").forEach((input) => {
      tx[input.dataset.field] = input.tagName === "SELECT" ? input.value : input.value;
    });
    transactions.push(tx);
  });

  if (!transactions.length) {
    statusEl.textContent = "Keine Zeilen ausgewaehlt.";
    statusEl.className = "warn";
    return;
  }

  commitBtn.disabled = true;
  statusEl.textContent = "Trage ein ...";
  statusEl.className = "";

  try {
    const res = await fetch("/commit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transactions }),
    });
    const data = await res.json();
    if (!res.ok) {
      statusEl.textContent = data.error || "Fehler beim Eintragen.";
      statusEl.className = "err";
    } else {
      statusEl.textContent = `${data.inserted} Zeilen ins Sheet eingetragen.`;
      statusEl.className = "ok";
    }
  } catch (err) {
    statusEl.textContent = "Netzwerkfehler: " + err;
    statusEl.className = "err";
  } finally {
    commitBtn.disabled = false;
  }
});
