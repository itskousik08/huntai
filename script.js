/* ================================================
   HUNTAI — Main JavaScript v2.0
   Hunt Your Best Version
   ================================================ */

'use strict';

/* ── Navbar Scroll Behavior ── */
(function initNavbar() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;

  const onScroll = () => {
    if (window.scrollY > 24) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

/* ── Mobile Menu Toggle ── */
(function initMobileMenu() {
  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');
  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', () => {
    const isOpen = hamburger.classList.toggle('open');
    mobileMenu.classList.toggle('open');
    hamburger.setAttribute('aria-expanded', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      mobileMenu.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    });
  });

  document.addEventListener('click', (e) => {
    if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
      hamburger.classList.remove('open');
      mobileMenu.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }
  });
})();

/* ── Active Nav Link ── */
(function initActiveNav() {
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a, .mobile-menu a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });
})();

/* ── Scroll Reveal ── */
(function initScrollReveal() {
  const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  if (!revealEls.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  revealEls.forEach(el => observer.observe(el));
})();

/* ── Animated Counters ── */
(function initCounters() {
  const statNums = document.querySelectorAll('.stat-num[data-target]');
  if (!statNums.length) return;

  const animateCounter = (el) => {
    const target = parseInt(el.getAttribute('data-target'), 10);
    const suffix = el.getAttribute('data-suffix') || '';
    const duration = 2000;
    const start = performance.now();

    const update = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 4);
      el.textContent = Math.round(eased * target).toLocaleString() + suffix;
      if (progress < 1) requestAnimationFrame(update);
    };

    requestAnimationFrame(update);
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  statNums.forEach(el => observer.observe(el));
})();

/* ── Progress Bar Animations ── */
(function initProgressBars() {
  const bars = document.querySelectorAll('.progress-bar[data-width]');
  if (!bars.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bar = entry.target;
        setTimeout(() => {
          bar.style.width = bar.getAttribute('data-width') + '%';
        }, 250);
        observer.unobserve(bar);
      }
    });
  }, { threshold: 0.35 });

  bars.forEach(bar => observer.observe(bar));
})();

/* ── Reading Progress Bar ── */
(function initReadingProgress() {
  const progressEl = document.getElementById('readingProgress');
  if (!progressEl) return;

  window.addEventListener('scroll', () => {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = window.scrollY;
    const progress = docHeight > 0 ? (scrolled / docHeight) * 100 : 0;
    progressEl.style.width = progress + '%';
  }, { passive: true });
})();

/* ── Smooth Scroll ── */
(function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const targetId = anchor.getAttribute('href').slice(1);
      const target = document.getElementById(targetId);
      if (target) {
        e.preventDefault();
        const offset = 100;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
})();

/* ── Glass Card Glow Effect ── */
(function initCardGlow() {
  const cards = document.querySelectorAll('.glass-card');
  if (window.matchMedia('(hover: none)').matches) return;

  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      card.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(99,102,241,0.06) 0%, var(--glass-bg) 55%)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.background = '';
    });
  });
})();

/* ── FAQ Accordion ── */
(function initFAQ() {
  const faqItems = document.querySelectorAll('.faq-item');
  if (!faqItems.length) return;

  faqItems.forEach(item => {
    const btn = item.querySelector('.faq-question');
    const answer = item.querySelector('.faq-answer');
    if (!btn || !answer) return;

    btn.addEventListener('click', () => {
      const isOpen = item.classList.contains('open');

      // Close all
      faqItems.forEach(other => {
        other.classList.remove('open');
        const otherBtn = other.querySelector('.faq-question');
        const otherAnswer = other.querySelector('.faq-answer');
        if (otherBtn) otherBtn.setAttribute('aria-expanded', 'false');
        if (otherAnswer) otherAnswer.setAttribute('aria-hidden', 'true');
      });

      // Open clicked (if it was closed)
      if (!isOpen) {
        item.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
        answer.setAttribute('aria-hidden', 'false');
      }
    });
  });
})();

/* ── Floating Contact Panel ── */
(function initFloatContact() {
  const btn = document.getElementById('floatBtn');
  const panel = document.getElementById('floatPanel');
  const closeBtn = document.getElementById('floatClose');
  if (!btn || !panel) return;

  const openPanel = () => {
    panel.classList.add('visible');
    panel.setAttribute('aria-hidden', 'false');
    btn.setAttribute('aria-expanded', 'true');
    btn.classList.add('active');
  };

  const closePanel = () => {
    panel.classList.remove('visible');
    panel.setAttribute('aria-hidden', 'true');
    btn.setAttribute('aria-expanded', 'false');
    btn.classList.remove('active');
  };

  btn.addEventListener('click', () => {
    panel.classList.contains('visible') ? closePanel() : openPanel();
  });

  if (closeBtn) closeBtn.addEventListener('click', closePanel);

  document.addEventListener('click', (e) => {
    const wrapper = document.getElementById('floatContact');
    if (wrapper && !wrapper.contains(e.target)) closePanel();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePanel();
  });
})();

/* ── Sticky Mobile Ad Close ── */
(function initStickyAd() {
  const ad = document.getElementById('adStickyMobile');
  const closeBtn = document.getElementById('adStickyClose');
  if (!ad || !closeBtn) return;

  closeBtn.addEventListener('click', () => {
    ad.style.display = 'none';
  });
})();

/* ── Parallax Blobs ── */
(function initParallaxBlobs() {
  const blobs = document.querySelectorAll('.blob');
  if (!blobs.length || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  let ticking = false;
  window.addEventListener('mousemove', (e) => {
    if (!ticking) {
      requestAnimationFrame(() => {
        const x = (e.clientX / window.innerWidth - 0.5);
        const y = (e.clientY / window.innerHeight - 0.5);
        blobs.forEach((blob, i) => {
          const factor = (i + 1) * 14;
          blob.style.transform = `translate(${x * factor}px, ${y * factor}px)`;
        });
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
})();

/* ── Pricing → mailto ── */
(function initPricingButtons() {
  document.querySelectorAll('.pricing-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const plan = btn.closest('.pricing-card')?.querySelector('.pricing-period')?.textContent || 'a plan';
      const price = btn.closest('.pricing-card')?.querySelector('.pricing-price')?.textContent || '';
      const subject = encodeURIComponent(`HUNTAI Subscription — ${plan.trim()} (${price.trim()})`);
      const body = encodeURIComponent(`Hi,\n\nI'd like to subscribe to the HUNTAI ${plan.trim()} plan at ${price.trim()}.\n\nPlease send me payment details.\n\nThank you.`);
      window.location.href = `mailto:kousikdebnath543@gmail.com?subject=${subject}&body=${body}`;
    });
  });
})();

/* ── Contact Form ── */
(function initContactForm() {
  const form = document.getElementById('contactForm');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = form.querySelector('#name')?.value?.trim();
    const email = form.querySelector('#email')?.value?.trim();
    const message = form.querySelector('#message')?.value?.trim();

    if (!name || !email || !message) {
      showFormMsg(form, 'Please fill in all fields.', 'error');
      return;
    }

    const subject = encodeURIComponent(`HUNTAI Message from ${name}`);
    const body = encodeURIComponent(`Name: ${name}\nEmail: ${email}\n\nMessage:\n${message}`);
    window.location.href = `mailto:kousikdebnath543@gmail.com?subject=${subject}&body=${body}`;
    showFormMsg(form, 'Opening your email client...', 'success');
    form.reset();
  });

  function showFormMsg(form, text, type) {
    let msg = form.querySelector('.form-msg');
    if (!msg) {
      msg = document.createElement('div');
      msg.className = 'form-msg';
      form.appendChild(msg);
    }
    msg.textContent = text;
    msg.style.cssText = `
      padding: 12px 18px;
      border-radius: 10px;
      margin-top: 14px;
      font-size: 0.9rem;
      font-weight: 600;
      background: ${type === 'success' ? 'rgba(34,197,94,0.09)' : 'rgba(239,68,68,0.09)'};
      color: ${type === 'success' ? '#16a34a' : '#dc2626'};
      border: 1px solid ${type === 'success' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'};
    `;
    setTimeout(() => { if (msg) msg.remove(); }, 4500);
  }
})();
