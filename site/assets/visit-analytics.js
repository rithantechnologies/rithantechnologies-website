/* Rithan website aggregate analytics (no cookies, IDs, or raw contact targets). */
(() => {
  "use strict";
  const nav = navigator;
  // Respect browser privacy signals before registering any tracking.
  if (nav.globalPrivacyControl === true || nav.doNotTrack === "1" || nav.doNotTrack === "yes") return;

  const pages = Object.freeze({
    "/": "home",
    "/whatsapp-ai/": "whatsapp-ai",
    "/privacy/": "privacy",
    "/terms/": "terms",
    "/rithan-ai/privacy/": "ai-privacy",
    "/rithan-ai/data-deletion/": "ai-deletion"
  });

  // Page labels are allowlisted; never send the URL, query string or hash.
  const pathname = location.pathname.replace(/\/index\.html$/i, "/");
  const normalized = pathname.endsWith("/") ? pathname : pathname + "/";
  const page = pages[normalized];
  if (!page) return;

  function track(type, channel) {
    const route = type === "page" ? "page/" + page : "contact/" + page + "/" + channel;
    // Fixed, non-identifying route. No cookies, payload, fingerprint or session ID.
    try {
      void fetch("/__rt_events/" + route, {
        method: "POST",
        mode: "same-origin",
        credentials: "omit",
        cache: "no-store",
        keepalive: true,
        referrerPolicy: "no-referrer"
      }).catch(() => {});
    } catch (_) {
      // Analytics must never interfere with navigation or contact actions.
    }
  }

  function contactChannel(href) {
    try {
      const target = new URL(href, document.baseURI);
      if (target.protocol === "tel:") return "phone";
      if (target.protocol === "mailto:") return "email";
      const host = target.hostname.toLowerCase();
      if (target.protocol === "https:" &&
          (host === "wa.me" || host === "api.whatsapp.com" ||
           host === "web.whatsapp.com" || host === "www.whatsapp.com")) {
        return "whatsapp";
      }
    } catch (_) {}
    return null;
  }

  document.addEventListener("click", (event) => {
    const target = event.target;
    const anchor = target && target.closest && target.closest("a[href]");
    if (!anchor) return;
    const channel = contactChannel(anchor.href);
    if (channel) track("contact", channel);
  }, true);

  // For homepage forms that open WhatsApp programmatically rather than via an <a>.
  window.RithanWebsiteAnalytics = Object.freeze({
    contact(channel) {
      if (channel === "phone" || channel === "email" || channel === "whatsapp") {
        track("contact", channel);
      }
    }
  });

  track("page");
})();
