const screen = document.getElementById("screen");
const exprEl = document.getElementById("expr");
const list = document.getElementById("historyList");
const empty = document.getElementById("empty");
let expr = "";
const pretty = s => s.replace(/\*/g, "×").replace(/\//g, "÷");

function render() {
  screen.classList.remove("error");
  screen.textContent = expr ? pretty(expr) : "0";
}
function showError(msg) {
  screen.textContent = msg; screen.classList.add("error"); expr = "";
}

async function equals() {
  if (!expr) return;
  try {
    const res = await fetch("/api/calculate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression: expr }),
    });
    const data = await res.json();
    if (!res.ok) return showError(data.error);
    exprEl.textContent = pretty(expr) + " =";
    expr = data.result; render();
    loadHistory();
  } catch { showError("Server not reachable"); }
}

function press(key) {
  const last = expr.slice(-1);
  if ("+-*/%".includes(key) && (!expr || "+-*/%".includes(last))) {
    if (!expr && key !== "-") return;
    if (expr) expr = expr.slice(0, -1);
  }
  expr += key; render();
}

document.getElementById("keys").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  if (b.dataset.key) press(b.dataset.key);
  else if (b.dataset.act === "clear") { expr = ""; exprEl.textContent = ""; render(); }
  else if (b.dataset.act === "back") { expr = expr.slice(0, -1); render(); }
  else if (b.dataset.act === "equals") equals();
});

document.addEventListener("keydown", e => {
  if (/^[0-9.+\-*/%]$/.test(e.key)) press(e.key);
  else if (e.key === "Enter" || e.key === "=") { e.preventDefault(); equals(); }
  else if (e.key === "Backspace") { expr = expr.slice(0, -1); render(); }
  else if (e.key === "Escape") { expr = ""; exprEl.textContent = ""; render(); }
});

async function loadHistory() {
  const rows = await (await fetch("/api/history")).json();
  list.innerHTML = "";
  empty.hidden = rows.length > 0;
  rows.forEach(r => {
    const li = document.createElement("li");
    const small = document.createElement("small"); small.textContent = pretty(r.expression);
    const strong = document.createElement("strong"); strong.textContent = "= " + r.result;
    li.append(small, strong);
    li.addEventListener("click", () => { expr = r.result; render(); });
    list.appendChild(li);
  });
}
document.getElementById("clearHistory").addEventListener("click", async () => {
  await fetch("/api/history", { method: "DELETE" }); loadHistory();
});
loadHistory();
