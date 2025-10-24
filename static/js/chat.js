const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const statusMessage = document.getElementById("statusMessage");
const loadingIndicator = document.getElementById("loadingIndicator");
const messageTemplate = document.getElementById("messageTemplate");

let conversationHistory = [];

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function appendMessage(role, content, timestamp = new Date()) {
  const template = messageTemplate.content.cloneNode(true);
  const article = template.querySelector(".message");
  const author = template.querySelector(".message__author");
  const body = template.querySelector(".message__body");
  const time = template.querySelector(".message__timestamp");

  article.classList.add(`message--${role}`);
  author.textContent = role === "assistant" ? "Neuro AI" : "You";
  body.innerHTML = renderMessageContent(content);
  time.textContent = formatTime(timestamp);

  chatWindow.appendChild(template);
  chatWindow.scrollTo({ top: chatWindow.scrollHeight, behavior: "smooth" });

  typesetMath(body);
}

function configureMarkdown() {
  if (typeof marked === "undefined") {
    return;
  }

  if (configureMarkdown.initialized) {
    return;
  }

  marked.setOptions({ breaks: true, gfm: true });
  configureMarkdown.initialized = true;
}

function renderMessageContent(content = "") {
  const text = content.trim();
  if (!text) {
    return "";
  }

  configureMarkdown();

  let html = text.replace(/\n/g, "<br />");

  if (typeof marked !== "undefined") {
    html = marked.parse(text);
  }

  if (typeof DOMPurify !== "undefined") {
    html = DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
  }

  return html;
}

function typesetMath(element) {
  if (!element || typeof window.MathJax === "undefined") {
    return;
  }

  const mathJax = window.MathJax;

  if (typeof mathJax.typesetPromise === "function") {
    mathJax.typesetPromise([element]).catch(() => {});
  } else if (typeof mathJax.typeset === "function") {
    mathJax.typeset([element]);
  }
}

function setLoading(isLoading) {
  loadingIndicator.hidden = !isLoading;
  userInput.disabled = isLoading;
  chatForm.querySelector("button[type='submit']").disabled = isLoading;
}

function setStatus(message = "") {
  statusMessage.textContent = message;
}

function autoResizeTextarea() {
  userInput.style.height = "auto";
  userInput.style.height = `${userInput.scrollHeight}px`;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = userInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  userInput.value = "";
  autoResizeTextarea();

  setLoading(true);
  setStatus("Consulting Neuro AI...");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history: conversationHistory }),
    });

    let data = {};
    try {
      data = await response.json();
    } catch (parseError) {
      // Ignore JSON parsing issues; handled below when checking response.ok.
    }

    if (!response.ok) {
      throw new Error(data.error || `Unexpected error (status ${response.status}).`);
    }

    conversationHistory = data.history || [];
    const assistantReply = conversationHistory[conversationHistory.length - 1];
    if (assistantReply?.role === "assistant") {
      appendMessage("assistant", assistantReply.content);
    }

    setStatus("Ready for your next idea.");
  } catch (error) {
    setStatus(error.message || "Unable to reach Neuro AI.");
  } finally {
    setLoading(false);
  }
});

userInput.addEventListener("input", autoResizeTextarea);

window.addEventListener("DOMContentLoaded", () => {
  const welcomeMessage =
    "Hello, I'm Neuro AI. Share your goals, and I'll help you strategize, write, or build with clarity.";
  appendMessage("assistant", welcomeMessage);
  conversationHistory.push({ role: "assistant", content: welcomeMessage });
  autoResizeTextarea();
  setStatus("Online");
});
