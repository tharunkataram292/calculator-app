const expressionDisplay = document.querySelector("#expression");
const resultDisplay = document.querySelector("#result");
const errorDisplay = document.querySelector("#error-message");
const historyToggle = document.querySelector("#history-toggle");
const historyPanel = document.querySelector("#history-panel");
const historyList = document.querySelector("#history-list");

const HISTORY_KEY = "calc-history";
const MAX_HISTORY_ITEMS = 8;
let expression = "";
let result = "0";
let justCalculated = false;
let history = loadHistory();

function loadHistory() {
  try {
    const stored = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    if (!Array.isArray(stored)) return [];
    return stored.filter(
      (item) =>
        item &&
        typeof item.expression === "string" &&
        typeof item.result === "string",
    ).slice(0, MAX_HISTORY_ITEMS);
  } catch {
    return [];
  }
}

function saveHistory() {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch {
    showError("Could not save calculation history in this browser.");
  }
}

function pretty(value) {
  return value.replace(/\*/g, "×").replace(/\//g, "÷").replace(/-/g, "−");
}

function render() {
  expressionDisplay.textContent = expression ? pretty(expression) : "0";
  resultDisplay.textContent = result;
}

function showError(message) {
  errorDisplay.textContent = message;
  errorDisplay.hidden = false;
}

function clearError() {
  errorDisplay.textContent = "";
  errorDisplay.hidden = true;
}

function clearAll() {
  expression = "";
  result = "0";
  justCalculated = false;
  clearError();
  render();
}

function appendValue(value) {
  clearError();
  if (justCalculated && /[\d.(]/.test(value)) {
    expression = "";
    result = "0";
  }
  justCalculated = false;

  if (value === ".") {
    const currentNumber = expression.split(/[+\-*/()]/).pop() || "";
    if (currentNumber.includes(".")) return;
    if (!currentNumber) expression += "0";
  }

  if (/[+\-*/]/.test(value) && expression && /[+\-*/.]$/.test(expression)) {
    if (value === "-" && /[*/]$/.test(expression)) {
      expression += value;
    } else {
      expression = expression.slice(0, -1) + value;
    }
  } else {
    expression += value;
  }
  render();
}

function deleteLast() {
  clearError();
  if (justCalculated) {
    clearAll();
    return;
  }
  expression = expression.slice(0, -1);
  result = expression || "0";
  render();
}

function toggleSign() {
  clearError();
  if (!expression || justCalculated) {
    if (justCalculated) {
      result = result.startsWith("-") ? result.slice(1) : `-${result}`;
      expression = result;
      justCalculated = true;
    } else {
      expression = "-";
    }
  } else {
    const match = expression.match(/(?:^|[+\-*/(])(-?(?:\d+\.?\d*|\.\d+))$/);
    if (!match) return;
    const start = expression.length - match[1].length;
    const unsigned = match[1].startsWith("-") ? match[1].slice(1) : `-${match[1]}`;
    expression = expression.slice(0, start) + unsigned;
  }
  render();
}

function togglePercent() {
  clearError();
  if (!expression || justCalculated) {
    if (result === "0") return;
    expression = `(${result})/100`;
    justCalculated = false;
  } else {
    const match = expression.match(/(?:^|[+\-*/(])(-?(?:\d+\.?\d*|\.\d+))$/);
    if (!match) return;
    const start = expression.length - match[1].length;
    expression = `${expression.slice(0, start)}(${match[1]}/100)`;
  }
  render();
}

function applyFunction(name) {
  clearError();
  const value = justCalculated ? result : expression;
  if (!value) return;
  expression = name === "square" ? `(${value})**2` : `sqrt(${value})`;
  justCalculated = false;
  render();
}

function renderHistory() {
  historyList.replaceChildren();
  for (const item of history) {
    const row = document.createElement("li");
    const button = document.createElement("button");
    const expressionText = document.createElement("span");
    const resultText = document.createElement("span");
    button.type = "button";
    button.className = "history-entry";
    expressionText.className = "history-expression";
    expressionText.textContent = pretty(item.expression);
    resultText.className = "history-result";
    resultText.textContent = item.result;
    button.append(expressionText, resultText);
    button.addEventListener("click", () => {
      expression = item.expression;
      result = item.result;
      justCalculated = true;
      clearError();
      render();
      historyPanel.hidden = true;
      historyToggle.setAttribute("aria-expanded", "false");
    });
    row.append(button);
    historyList.append(row);
  }
  if (history.length === 0) {
    const empty = document.createElement("li");
    empty.className = "history-expression";
    empty.textContent = "No calculations yet";
    historyList.append(empty);
  }
}

async function calculate() {
  if (!expression.trim()) return;
  clearError();
  try {
    const response = await fetch("/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ expression }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Calculation failed.");

    result = data.result;
    history = [
      { expression, result },
      ...history.filter((item) => item.expression !== expression),
    ].slice(0, MAX_HISTORY_ITEMS);
    saveHistory();
    renderHistory();
    justCalculated = true;
    render();
  } catch (error) {
    showError(error instanceof Error ? error.message : "Unable to calculate right now.");
  }
}

document.querySelector(".keypad").addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.value !== undefined) {
    appendValue(button.dataset.value);
    return;
  }
  switch (button.dataset.action) {
    case "clear":
      clearAll();
      break;
    case "delete":
      deleteLast();
      break;
    case "sign":
      toggleSign();
      break;
    case "percent":
      togglePercent();
      break;
    case "sqrt":
      applyFunction("sqrt");
      break;
    case "square":
      applyFunction("square");
      break;
    case "equals":
      calculate();
      break;
  }
});

historyToggle.addEventListener("click", () => {
  const expanded = historyToggle.getAttribute("aria-expanded") === "true";
  historyToggle.setAttribute("aria-expanded", String(!expanded));
  historyPanel.hidden = expanded;
  renderHistory();
});

document.querySelector("#clear-history").addEventListener("click", () => {
  history = [];
  saveHistory();
  renderHistory();
});

document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  if (/^\d$/.test(event.key) || [".", "+", "-", "*", "/", "(", ")"].includes(event.key)) {
    event.preventDefault();
    appendValue(event.key);
  } else if (event.key === "Enter" || event.key === "=") {
    event.preventDefault();
    calculate();
  } else if (event.key === "Backspace") {
    event.preventDefault();
    deleteLast();
  } else if (event.key === "Escape") {
    clearAll();
  } else if (event.key === "%") {
    togglePercent();
  }
});

render();
renderHistory();
