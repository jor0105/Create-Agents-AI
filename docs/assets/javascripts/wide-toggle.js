/* Wide mode toggle for MkDocs Material */
(function () {
  var storageKey = "ai_agent_wide_mode";
  var html = document.documentElement;

  function applyPreference(value) {
    if (value) {
      document.body.classList.add("wide-mode");
    } else {
      document.body.classList.remove("wide-mode");
    }
  }

  function createToggle() {
    var btn = document.createElement("button");
    btn.className = "md-header__button md-icon";
    btn.title = "Alternar largura ampla";
    btn.setAttribute("aria-label", "Alternar largura ampla");
    btn.innerHTML =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path fill="currentColor" d="M3 5h18v2H3V5zm0 12h18v2H3v-2zm4-7h10v4H7v-4z"/></svg>';
    btn.addEventListener("click", function () {
      var next = !document.body.classList.contains("wide-mode");
      applyPreference(next);
      try {
        localStorage.setItem(storageKey, next ? "1" : "0");
      } catch (e) {}
    });
    return btn;
  }

  function mountToggle() {
    var header = document.querySelector(".md-header__inner");
    if (!header) return;
    var container = header.querySelector(".md-header__option");
    var target = container || header;
    target.appendChild(createToggle());
  }

  document.addEventListener("DOMContentLoaded", function () {
    var pref = null;
    try {
      pref = localStorage.getItem(storageKey);
    } catch (e) {}
    applyPreference(pref === "1");
    mountToggle();
  });
})();
