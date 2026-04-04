/* ================================================
   HUNTAI — Main JavaScript
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
  onScroll(); // run on load
})();

/* ── Mobile Menu Toggle ── */
(function initMobileMenu() {
  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');
  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('open');
    mobileMenu.classList.toggle('open');
    document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
  });

  // Close on link click
  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
      hamburger.classList.remove('open');
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    }
  });
})();

/* ── Active Nav Link Highlighting ── */
(function initActiveNav() {
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  const navLinks = document.querySelectorAll('.nav-links a, .mobile-menu a');

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });
})();

/* ── Scroll Reveal (Intersection Observer) ── */
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
  }, {
    threshold: 0.12,
    rootMargin: '0px 0px -40px 0px'
  });

  revealEls.forEach(el => observer.observe(el));
})();

/* ── Animated Counters ── */
(function initCounters() {
  const statNums = document.querySelectorAll('.stat-num[data-target]');
  if (!statNums.length) return;

  const animateCounter = (el) => {
    const target = parseInt(el.getAttribute('data-target'), 10);
    const suffix = el.getAttribute('data-suffix') || '';
    const duration = 1800;
    const start = performance.now();

    const update = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
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
        }, 200);
        observer.unobserve(bar);
      }
    });
  }, { threshold: 0.4 });

  bars.forEach(bar => observer.observe(bar));
})();

/* ── Smooth Scroll for anchor links ── */
(function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const targetId = anchor.getAttribute('href').slice(1);
      const target = document.getElementById(targetId);
      if (target) {
        e.preventDefault();
        const offset = 88;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
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

    // Build mailto link and open
    const subject = encodeURIComponent(`HUNTAI Message from ${name}`);
    const body = encodeURIComponent(`Name: ${name}\nEmail: ${email}\n\nMessage:\n${message}`);
    window.location.href = `mailto:kousikdebnath543@gmail.com?subject=${subject}&body=${body}`;

    showFormMsg(form, '✓ Opening your email client...', 'success');
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
      padding: 12px 16px;
      border-radius: 10px;
      margin-top: 12px;
      font-size: 0.9rem;
      font-weight: 500;
      background: ${type === 'success' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)'};
      color: ${type === 'success' ? '#16a34a' : '#dc2626'};
      border: 1px solid ${type === 'success' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'};
    `;
    setTimeout(() => { if (msg) msg.remove(); }, 4000);
  }
})();

/* ── Parallax Blobs (subtle) ── */
(function initParallaxBlobs() {
  const blobs = document.querySelectorAll('.blob');
  if (!blobs.length || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  window.addEventListener('mousemove', (e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 1;
    const y = (e.clientY / window.innerHeight - 0.5) * 1;

    blobs.forEach((blob, i) => {
      const factor = (i + 1) * 12;
      blob.style.transform = `translate(${x * factor}px, ${y * factor}px)`;
    });
  }, { passive: true });
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

/* ── Glassmorphism card glow on hover ── */
(function initCardGlow() {
  const cards = document.querySelectorAll('.glass-card');

  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      card.style.background = `radial-gradient(circle at ${x}% ${y}%, rgba(99,102,241,0.07) 0%, var(--glass-bg) 60%)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.background = '';
    });
  });
})();

/* ── Pricing Click → mailto ── */
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

/* ── Lazy load ad scripts ── */
(function lazyLoadAds() {
  // Defer ad loading slightly for performance
  window.addEventListener('load', () => {
    setTimeout(() => {
      document.querySelectorAll('[data-ad-src]').forEach(el => {
        const script = document.createElement('script');
        script.src = el.getAttribute('data-ad-src');
        script.async = true;
        el.appendChild(script);
      });
    }, 1200);
  });
})();
