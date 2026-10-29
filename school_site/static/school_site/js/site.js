(function () {
  "use strict";
  const config = window.SCHOOL_CONFIG || {};
  const toast = document.getElementById("siteToast");
  let toastTimer;

  function notify(title, message) {
    if (!toast) return;
    toast.innerHTML = '<span class="toast-title"></span><span class="toast-message"></span>';
    toast.querySelector(".toast-title").textContent = title;
    toast.querySelector(".toast-message").textContent = message;
    toast.classList.add("show");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove("show"), 4600);
  }

  document.querySelectorAll("[data-current-year]").forEach((el) => {
    el.textContent = String(new Date().getFullYear());
  });

  const phone = (config.telephone || "").trim();
  const email = (config.email || "").trim();
  const schoolMapUrl = "https://www.google.com/maps/search/?api=1&query=-20.80019745107235%2C30.79963980896671";

  document.querySelectorAll(".footer-main .col-lg-3").forEach((column) => {
    const heading = column.querySelector(".footer-heading");
    const location = column.querySelector(".footer-contact-line");
    if (!heading || heading.textContent.trim() !== "Find the school" || !location) return;

    const mapLink = document.createElement("a");
    mapLink.className = location.className;
    mapLink.href = schoolMapUrl;
    mapLink.target = "_blank";
    mapLink.rel = "noopener noreferrer";
    mapLink.setAttribute("aria-label", "Find Ngundu Halt Government High School on Google Maps");
    while (location.firstChild) mapLink.append(location.firstChild);
    location.replaceWith(mapLink);
  });

  const locationPanel = document.querySelector(".location-panel");
  const mapPlaceholder = locationPanel?.querySelector(".placeholder-chip");
  if (mapPlaceholder) {
    const mapLink = document.createElement("a");
    mapLink.className = "text-link";
    mapLink.href = schoolMapUrl;
    mapLink.target = "_blank";
    mapLink.rel = "noopener noreferrer";
    mapLink.textContent = "Open exact location in Google Maps";
    mapPlaceholder.replaceWith(mapLink);

    const directions = locationPanel.querySelector(".location-panel-right p");
    if (directions) directions.textContent = "-20.80019745107235, 30.79963980896671";
  }

  document.querySelectorAll("[data-school-phone]").forEach((el) => {
    if (phone) {
      el.textContent = phone;
      if (el.tagName === "A") el.href = "tel:" + phone.replace(/[^+\d]/g, "");
    }
  });
  document.querySelectorAll("[data-school-email]").forEach((el) => {
    if (email) {
      el.textContent = email;
      if (el.tagName === "A") el.href = "mailto:" + email;
    }
  });

  document.querySelectorAll("[data-results-portal]").forEach((link) => {
    const url = (config.resultsPortalUrl || "").trim();
    if (url) {
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.removeAttribute("aria-disabled");
    } else {
      link.setAttribute("aria-disabled", "true");
      link.addEventListener("click", (event) => {
        event.preventDefault();
        notify("Results portal not connected", "Add the school's existing results portal URL in assets/js/config.js before launch.");
      });
    }
  });

  const portalNote = document.getElementById("portalConfigurationNote");
  if ((config.resultsPortalUrl || "").trim() && portalNote) {
    portalNote.textContent = "The portal link is configured and opens in a new tab.";
  }

  document.querySelectorAll("[data-staff-access]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      notify("Staff access", "The Django admin route will be enabled after the website is integrated with the school's backend. It is intentionally not a public header button.");
    });
  });

  // Teachers directory search/filter.
  const teacherSearch = document.getElementById("teacherSearch");
  if (teacherSearch) {
    const cards = Array.from(document.querySelectorAll("[data-teacher-card]"));
    const count = document.getElementById("teacherSearchCount");
    const noResults = document.getElementById("teacherNoResults");
    teacherSearch.addEventListener("input", () => {
      const query = teacherSearch.value.trim().toLowerCase();
      let visible = 0;
      cards.forEach((card) => {
        const haystack = (card.textContent + " " + (card.dataset.search || "")).toLowerCase();
        const match = !query || haystack.includes(query);
        card.classList.toggle("d-none", !match);
        if (match) visible += 1;
      });
      if (count) count.textContent = visible + (visible === 1 ? " department card" : " department cards");
      if (noResults) noResults.classList.toggle("d-none", visible !== 0);
    });
  }

  // Gallery filters and accessible Bootstrap modal lightbox.
  const galleryFilters = document.querySelectorAll("[data-gallery-filter]");
  const galleryTiles = document.querySelectorAll("[data-gallery-image]");
  galleryFilters.forEach((button) => {
    button.addEventListener("click", () => {
      galleryFilters.forEach((item) => item.classList.toggle("active", item === button));
      const selected = button.dataset.galleryFilter;
      galleryTiles.forEach((tile) => {
        const matches = selected === "all" || tile.dataset.galleryCategory === selected;
        tile.hidden = !matches;
      });
    });
  });
  const galleryModalEl = document.getElementById("galleryModal");
  if (galleryModalEl && window.bootstrap) {
    const modal = new bootstrap.Modal(galleryModalEl);
    const modalImage = document.getElementById("galleryModalImage");
    const modalCaption = document.getElementById("galleryModalCaption");
    galleryTiles.forEach((tile) => {
      tile.addEventListener("click", () => {
        modalImage.src = tile.dataset.galleryImage;
        modalImage.alt = tile.dataset.galleryCaption || "School gallery image";
        modalCaption.textContent = tile.dataset.galleryCaption || "School gallery";
        modal.show();
      });
    });
    galleryModalEl.addEventListener("hidden.bs.modal", () => {
      modalImage.src = "";
      modalImage.alt = "";
    });
  }

  // Front-end validation for the presentation-only contact form.
  const contactForm = document.getElementById("contactForm");
  if (contactForm) {
    contactForm.addEventListener("submit", (event) => {
      event.preventDefault();
      event.stopPropagation();
      contactForm.classList.add("was-validated");
      const feedback = document.getElementById("contactFeedback");
      if (!contactForm.checkValidity()) {
        if (feedback) {
          feedback.className = "form-feedback mt-3 is-visible";
          feedback.textContent = "Please complete the required fields. This preview validates the form locally only.";
        }
        return;
      }
      if (feedback) {
        feedback.className = "form-feedback mt-3 is-visible";
        feedback.textContent = "Thank you. This demo form is not connected to email or storage yet; the Django backend will handle submissions after integration.";
      }
      contactForm.reset();
      contactForm.classList.remove("was-validated");
    });
  }

  // Keep opening a dropdown from its current submenu accessible on touch screens.
  document.querySelectorAll(".navbar .dropdown-toggle").forEach((toggle) => {
    toggle.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        const firstItem = toggle.nextElementSibling?.querySelector(".dropdown-item");
        if (firstItem && window.bootstrap) {
          bootstrap.Dropdown.getOrCreateInstance(toggle).show();
          firstItem.focus();
        }
      }
    });
  });
})();
