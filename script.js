const WHATSAPP_NUMBER = "51956758644";
const DEBUG_WHATSAPP = false;

const CONFIG = {
  letter:
    "Quería hacerte algo distinto. No solo una lista de planes, sino un pequeño lugar hecho para ti. Aquí puedes elegir cuál será nuestro próximo recuerdo, y yo me encargo del resto.",
  whatsappFinalLine: "Prometo encargarme de que sea un recuerdo bonito.",
  detailHints: {
    "Para quedarnos tranquis": "A veces el mejor plan es simplemente estar.",
    "Cine y películas": "Plan perfecto para apagar el mundo un rato.",
    "Comida y antojos": "Algo rico también puede ser un plan bonito.",
    "Noche, música y baile": "Una noche para soltarnos un poco.",
    "Diversión y juegos": "Risas, competencia y cero solemnidad.",
    Aventura: "Un recuerdo de esos que no se olvidan.",
    "Arte y experiencias": "Un plan para crear algo juntos.",
    "Planes random especiales": "Raro, inesperado y probablemente memorable.",
    "Fotos y lugares bonitos": "Para guardar este día en fotos bonitas."
  },
  categoryIcons: {
    "Para quedarnos tranquis": "☁️",
    "Cine y películas": "🎬",
    "Comida y antojos": "🍰",
    "Noche, música y baile": "🎵",
    "Diversión y juegos": "🎲",
    Aventura: "🌅",
    "Arte y experiencias": "🎨",
    "Planes random especiales": "✨",
    "Fotos y lugares bonitos": "📸"
  },
  assetFallbacks: {
    shrekOne: ["assets/shrek/shrek-01.png", "assets/grogu/shrek-01.png"],
    shrekTwo: ["assets/shrek/shrek-02.png", "assets/grogu/shrek-02.png"],
    grogu: ["assets/grogu/grogu-01.png"],
    jengi: ["assets/shrek/jengi-01.png", "assets/grogu/jengi-01.png"],
    turtle: ["assets/backgrounds/tortuga-nemo.png", "assets/grogu/tortuga-nemo.png"]
  },
  categoryAssets: {
    "Para quedarnos tranquis": "grogu",
    "Cine y películas": "turtle",
    "Comida y antojos": "jengi",
    "Noche, música y baile": "shrekTwo",
    "Diversión y juegos": "shrekOne",
    Aventura: "turtle",
    "Arte y experiencias": "jengi",
    "Planes random especiales": "shrekTwo",
    "Fotos y lugares bonitos": "grogu"
  },
  categoryVisuals: {
    "Para quedarnos tranquis": { slug: "tranquis", icon: "☁️", label: "calma" },
    "Cine y películas": { slug: "cine", icon: "🎬", label: "cine" },
    "Comida y antojos": { slug: "comida", icon: "🍰", label: "antojo" },
    "Noche, música y baile": { slug: "noche", icon: "🎵", label: "noche" },
    "Diversión y juegos": { slug: "juegos", icon: "🎲", label: "juego" },
    Aventura: { slug: "aventura", icon: "🌅", label: "aventura" },
    "Arte y experiencias": { slug: "arte", icon: "🎨", label: "arte" },
    "Planes random especiales": { slug: "random", icon: "✨", label: "sorpresa" },
    "Fotos y lugares bonitos": { slug: "fotos", icon: "📸", label: "foto" }
  }
};

const AUDIO_CONFIG = {
  ambient: "assets/audio/shrek-intro-long.mp3",
  open: "assets/audio/open.mp3",
  select: "assets/audio/select.mp3",
  surprise: "assets/audio/surprise.mp3",
  confirm: "assets/audio/confirm.mp3"
};

const AUDIO_VOLUME = {
  ambient: 0.14,
  effect: 0.28
};

const VISUAL_CONFIG = {
  mobileParticleCount: 34,
  desktopParticleCount: 62,
  canvasLights: 38
};

const CATEGORIES = [
  "Para quedarnos tranquis",
  "Cine y películas",
  "Comida y antojos",
  "Noche, música y baile",
  "Diversión y juegos",
  "Aventura",
  "Arte y experiencias",
  "Planes random especiales",
  "Fotos y lugares bonitos"
];

const PLANS = [
  {
    id: "noche-de-peliculas",
    title: "Noche de películas",
    category: "Cine y películas",
    description: "Películas, snacks, comodidad y pasarla bonito sin complicarnos."
  },
  {
    id: "ir-al-cine",
    title: "Ir al cine",
    category: "Cine y películas",
    description: "Puede ser cine tradicional, cine en la playa o cine 4D."
  },
  {
    id: "discoteca",
    title: "Discoteca",
    category: "Noche, música y baile",
    description: "Salir a bailar, despejarnos y vivir una noche diferente."
  },
  {
    id: "hacer-un-viaje",
    title: "Hacer un viaje",
    category: "Aventura",
    description: "Una escapada para cambiar de aire y crear un recuerdo grande."
  },
  {
    id: "salir-a-comer",
    title: "Salir a comer",
    category: "Comida y antojos",
    description: "Puede ser comer algo nuevo, una salida normal o que uno decida qué come el otro."
  },
  {
    id: "caminar-sin-rumbo",
    title: "Caminar sin rumbo",
    category: "Para quedarnos tranquis",
    description: "Salir sin destino fijo y dejar que el momento decida."
  },
  {
    id: "ir-a-tomar-unos-tragos",
    title: "Ir a tomar unos tragos",
    category: "Noche, música y baile",
    description: "Una salida relajada para conversar, brindar y pasarla bien."
  },
  {
    id: "modo-relax",
    title: "Modo relax",
    category: "Para quedarnos tranquis",
    description: "Sauna, masajes o un plan para desconectarnos de todo."
  },
  {
    id: "ir-a-los-juegos",
    title: "Ir a los juegos",
    category: "Diversión y juegos",
    description: "Juegos mecánicos, Coney Park, juegos inflables o algo parecido."
  },
  {
    id: "patinaje-sobre-hielo",
    title: "Patinaje sobre hielo",
    category: "Diversión y juegos",
    description: "Un plan diferente, divertido y con posibles caídas memorables."
  },
  {
    id: "bowling",
    title: "Bowling",
    category: "Diversión y juegos",
    description: "Competencia amistosa, risas y una excusa para molestarnos jugando."
  },
  {
    id: "pintar-y-manualidades",
    title: "Pintar y manualidades",
    category: "Arte y experiencias",
    description: "Hacer algo creativo y llevarnos un recuerdo hecho por nosotros."
  },
  {
    id: "cocinar-un-postre",
    title: "Cocinar un postre",
    category: "Comida y antojos",
    description: "Preparar algo dulce juntos, aunque salga perfecto o sea un desastre bonito."
  },
  {
    id: "ir-a-la-playa-para-ver-el-atardecer",
    title: "Ir a la playa para ver el atardecer",
    category: "Aventura",
    description: "Ir a la playa, ver el cielo cambiar de color y quedarnos un rato ahí."
  },
  {
    id: "hacer-un-en-vivo",
    title: "Hacer un en vivo",
    category: "Planes random especiales",
    description: "Hacer un live juntos, improvisar y ver qué pasa."
  },
  {
    id: "ir-a-un-concierto",
    title: "Ir a un concierto",
    category: "Noche, música y baile",
    description: "Música en vivo, emoción y una noche para recordar."
  },
  {
    id: "ir-a-un-stand-up",
    title: "Ir a un stand up",
    category: "Arte y experiencias",
    description: "Reírnos juntos y salir con frases internas nuevas."
  },
  {
    id: "plan-webing",
    title: "Plan webing",
    category: "Para quedarnos tranquis",
    description: "Simplemente existir juntos, sin presión, sin agenda y sin hacer mucho."
  },
  {
    id: "ir-a-un-karaoke",
    title: "Ir a un karaoke",
    category: "Noche, música y baile",
    description: "Cantar bien, cantar mal o simplemente hacer show."
  },
  {
    id: "ir-a-ver-lucha-libre",
    title: "Ir a ver lucha libre",
    category: "Planes random especiales",
    description: "Un plan intenso, raro y probablemente muy entretenido."
  },
  {
    id: "carrera-en-karts",
    title: "Carrera en karts",
    category: "Diversión y juegos",
    description: "Competir, acelerar y ver quién maneja mejor."
  },
  {
    id: "ir-a-un-game-center",
    title: "Ir a un game center",
    category: "Diversión y juegos",
    description: "Ir a un lugar con videojuegos, maquinitas y retos random."
  },
  {
    id: "hacer-parapente",
    title: "Hacer parapente",
    category: "Aventura",
    description: "Un plan extremo para ver todo desde arriba y recordar ese momento siempre."
  },
  {
    id: "ir-al-barrio-chino",
    title: "Ir al barrio chino",
    category: "Comida y antojos",
    description: "Comer, caminar, probar cosas y descubrir lugares."
  },
  {
    id: "jugar-tenis",
    title: "Jugar tenis",
    category: "Diversión y juegos",
    description: "Un plan activo para jugar, competir y divertirnos."
  },
  {
    id: "ir-a-lugares-pinterest",
    title: "Ir a lugares Pinterest",
    category: "Fotos y lugares bonitos",
    description: "Ir a lugares instagrameables para tomarnos fotos bonitas."
  },
  {
    id: "ir-a-bailar",
    title: "Ir a bailar",
    category: "Noche, música y baile",
    description: "Salir a movernos, reírnos y olvidarnos del resto."
  },
  {
    id: "ir-al-billar",
    title: "Ir al billar",
    category: "Diversión y juegos",
    description: "Una salida tranquila, competitiva y con buena conversación."
  },
  {
    id: "ir-a-un-escape-room",
    title: "Ir a un escape room",
    category: "Diversión y juegos",
    description: "Resolver pistas juntos y comprobar qué tan buen equipo somos."
  },
  {
    id: "ver-videos-de-youtube-en-su-casa",
    title: "Ver videos de YouTube en su casa",
    category: "Para quedarnos tranquis",
    description: "Videos random, risas, comodidad y cero producción."
  }
];

const screens = document.querySelectorAll(".screen");
const particles = document.querySelector("#particles");
const magicCanvas = document.querySelector("#magic-canvas");
const audioToggle = document.querySelector("#audio-toggle");
const plansGrid = document.querySelector("#plans-grid");
const categoryFilter = document.querySelector("#category-filter");
const searchInput = document.querySelector("#plan-search");
const showAllButton = document.querySelector("#show-all-btn");
const surpriseButton = document.querySelector("#surprise-btn");
const resultCount = document.querySelector("#result-count");
const toast = document.querySelector("#toast");
const letterText = document.querySelector("#letter-text");
const cursorGlow = document.querySelector("#cursor-glow");
const journeyDots = document.querySelectorAll(".journey-dot");

const detailImage = document.querySelector("#detail-image");
const detailTitle = document.querySelector("#detail-title");
const detailCategory = document.querySelector("#detail-category");
const detailDescription = document.querySelector("#detail-description");
const detailMeta = document.querySelector("#detail-meta");
const dateInput = document.querySelector("#date-input");
const commentInput = document.querySelector("#comment-input");
const prepareConfirmationButton = document.querySelector("#prepare-confirmation-btn");
const whatsappLink = document.querySelector("#whatsapp-link");
const copyMessageButton = document.querySelector("#copy-message-btn");
const confirmationSummary = document.querySelector("#confirmation-summary");

let activeCategory = "all";
let selectedPlan = null;
let ambientAudio = null;
let ambientFadeFrame = null;
let isMusicStarted = false;
let isAudioMuted = true;
let lastEffectAt = 0;

function normalizeText(value) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function showScreen(screenId) {
  screens.forEach((screen) => {
    screen.classList.toggle("is-active", screen.id === screenId);
  });

  document.body.dataset.screen = screenId;
  journeyDots.forEach((dot) => {
    dot.classList.toggle("is-active", dot.dataset.step === screenId);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function navigateTo(screenId, options = {}) {
  if (options.intro) {
    startIntroAudio();
    document.body.classList.add("is-opening-gift");
    window.setTimeout(() => {
      document.body.classList.remove("is-opening-gift");
      showScreen(screenId);
    }, 520);
    return;
  }

  showScreen(screenId);
}

function createFallback(label) {
  const fallback = document.createElement("div");
  fallback.className = "image-fallback";
  fallback.innerHTML = `<span>${label}</span>`;
  return fallback;
}

function getAssetSources(assetKey) {
  return CONFIG.assetFallbacks[assetKey] || [assetKey];
}

function setImage(container, assetKey, fallbackLabel) {
  container.replaceChildren();

  const sources = getAssetSources(assetKey);
  const img = document.createElement("img");
  let sourceIndex = 0;

  img.alt = fallbackLabel;
  img.loading = "lazy";
  img.decoding = "async";
  img.onerror = () => {
    sourceIndex += 1;
    if (sourceIndex < sources.length) {
      img.src = sources[sourceIndex];
      return;
    }
    container.replaceChildren(createFallback(fallbackLabel));
  };

  img.src = sources[sourceIndex];
  container.append(img);
}

function createCategoryVisual(category, title = category) {
  const visualData = CONFIG.categoryVisuals[category] || { slug: "random", icon: "✨", label: "magia" };
  const visual = document.createElement("div");
  visual.className = `category-visual category-visual-${visualData.slug}`;
  visual.setAttribute("aria-label", title);

  const halo = document.createElement("span");
  halo.className = "visual-halo";

  const orbit = document.createElement("span");
  orbit.className = "visual-orbit";

  const icon = document.createElement("span");
  icon.className = "visual-icon";
  icon.textContent = visualData.icon;

  const label = document.createElement("span");
  label.className = "visual-label";
  label.textContent = visualData.label;

  const glints = document.createElement("span");
  glints.className = "visual-glints";

  visual.append(halo, orbit, icon, label, glints);
  return visual;
}

function setCategorySticker(container, assetKey, fallbackLabel) {
  const sticker = document.createElement("div");
  sticker.className = "category-sticker";
  setImage(sticker, assetKey, fallbackLabel);
  container.append(sticker);
}

function setupAssetStickers() {
  document.querySelectorAll("[data-asset]").forEach((sticker) => {
    setImage(sticker, sticker.dataset.asset, sticker.dataset.fallback || "Magia");
  });
}

function setupParticles() {
  const particleCount = window.matchMedia("(max-width: 700px)").matches
    ? VISUAL_CONFIG.mobileParticleCount
    : VISUAL_CONFIG.desktopParticleCount;
  particles.replaceChildren();

  for (let index = 0; index < particleCount; index += 1) {
    const particle = document.createElement("span");
    particle.className = index % 5 === 0 ? "particle petal" : "particle";
    particle.style.setProperty("--x", `${Math.random() * 100}%`);
    particle.style.setProperty("--y", `${Math.random() * 100}%`);
    particle.style.setProperty("--delay", `${Math.random() * -10}s`);
    particle.style.setProperty("--duration", `${8 + Math.random() * 12}s`);
    particle.style.setProperty("--size", `${4 + Math.random() * 9}px`);
    particles.append(particle);
  }
}

function setupMagicCanvas() {
  if (!magicCanvas) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const context = magicCanvas.getContext("2d", { alpha: true });
  if (!context || reduceMotion) return;

  let width = 0;
  let height = 0;
  let lights = [];

  function resize() {
    const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    magicCanvas.width = Math.floor(width * pixelRatio);
    magicCanvas.height = Math.floor(height * pixelRatio);
    magicCanvas.style.width = `${width}px`;
    magicCanvas.style.height = `${height}px`;
    context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);

    lights = Array.from({ length: VISUAL_CONFIG.canvasLights }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      radius: 1.2 + Math.random() * 3.6,
      speed: 0.12 + Math.random() * 0.42,
      drift: -0.22 + Math.random() * 0.44,
      phase: Math.random() * Math.PI * 2,
      hue: Math.random() > 0.5 ? "255, 211, 107" : "255, 155, 189"
    }));
  }

  function draw(time) {
    context.clearRect(0, 0, width, height);
    lights.forEach((light) => {
      light.y -= light.speed;
      light.x += Math.sin(time * 0.001 + light.phase) * light.drift;
      if (light.y < -20) {
        light.y = height + 20;
        light.x = Math.random() * width;
      }

      const pulse = 0.45 + Math.sin(time * 0.002 + light.phase) * 0.28;
      const gradient = context.createRadialGradient(light.x, light.y, 0, light.x, light.y, light.radius * 9);
      gradient.addColorStop(0, `rgba(${light.hue}, ${0.38 + pulse * 0.22})`);
      gradient.addColorStop(1, `rgba(${light.hue}, 0)`);
      context.fillStyle = gradient;
      context.beginPath();
      context.arc(light.x, light.y, light.radius * 9, 0, Math.PI * 2);
      context.fill();
    });

    requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(draw);
}

function setupParallax() {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion) return;

  window.addEventListener("pointermove", (event) => {
    const x = (event.clientX / window.innerWidth - 0.5).toFixed(3);
    const y = (event.clientY / window.innerHeight - 0.5).toFixed(3);
    document.documentElement.style.setProperty("--parallax-x", x);
    document.documentElement.style.setProperty("--parallax-y", y);
    document.documentElement.style.setProperty("--cursor-x", `${event.clientX}px`);
    document.documentElement.style.setProperty("--cursor-y", `${event.clientY}px`);
    cursorGlow.classList.add("is-visible");
  });

  window.addEventListener("pointerleave", () => {
    cursorGlow.classList.remove("is-visible");
  });
}

function startIntroAudio() {
  isAudioMuted = false;
  updateAudioToggle();
  playEffect("open");
  startAmbientMusic();
}

function createAmbientAudio() {
  if (ambientAudio) return ambientAudio;

  ambientAudio = new Audio(AUDIO_CONFIG.ambient);
  ambientAudio.loop = true;
  ambientAudio.preload = "auto";
  ambientAudio.volume = 0;
  ambientAudio.addEventListener("error", () => {
    ambientAudio = null;
    isMusicStarted = false;
  }, { once: true });

  return ambientAudio;
}

function startAmbientMusic() {
  if (isAudioMuted || isMusicStarted) return;

  const audio = createAmbientAudio();
  if (!audio) return;

  isMusicStarted = true;
  audio.volume = 0;
  audio.play()
    .then(() => fadeAmbientTo(AUDIO_VOLUME.ambient, 1400))
    .catch(() => {
      isMusicStarted = false;
    });
}

function pauseAmbientMusic() {
  if (!ambientAudio) return;
  if (ambientFadeFrame) cancelAnimationFrame(ambientFadeFrame);
  ambientAudio.pause();
  isMusicStarted = false;
}

function fadeAmbientTo(targetVolume, duration = 700) {
  if (!ambientAudio) return;
  if (ambientFadeFrame) cancelAnimationFrame(ambientFadeFrame);

  const startVolume = ambientAudio.volume;
  const startTime = performance.now();

  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    ambientAudio.volume = startVolume + (targetVolume - startVolume) * eased;
    if (progress < 1) {
      ambientFadeFrame = requestAnimationFrame(tick);
    }
  }

  ambientFadeFrame = requestAnimationFrame(tick);
}

function setAudioMuted(nextMuted) {
  isAudioMuted = nextMuted;
  updateAudioToggle();

  if (isAudioMuted) {
    fadeAmbientTo(0, 360);
    window.setTimeout(() => {
      if (isAudioMuted) pauseAmbientMusic();
    }, 380);
    return;
  }

  startAmbientMusic();
}

function updateAudioToggle() {
  audioToggle.textContent = isAudioMuted ? "🔇" : "🔊";
  audioToggle.classList.toggle("is-muted", isAudioMuted);
  audioToggle.setAttribute("aria-pressed", String(!isAudioMuted));
  audioToggle.setAttribute("aria-label", isAudioMuted ? "Activar música" : "Silenciar música");
}

function playEffect(name) {
  if (isAudioMuted) return;

  const now = performance.now();
  if (now - lastEffectAt < 90) return;
  lastEffectAt = now;

  const src = AUDIO_CONFIG[name];
  if (!src) return;

  const audio = new Audio(src);
  audio.preload = "auto";
  audio.volume = AUDIO_VOLUME.effect;
  audio.play().catch(() => {});
}

function renderCategories() {
  categoryFilter.replaceChildren();

  const allButton = createCategoryButton("Ver todos", "all");
  allButton.classList.add("is-active");
  categoryFilter.append(allButton);

  CATEGORIES.forEach((category) => {
    categoryFilter.append(createCategoryButton(category, category));
  });
}

function createCategoryButton(label, category) {
  const button = document.createElement("button");
  button.className = "chip";
  button.type = "button";
  button.innerHTML = `<span>${category === "all" ? "✦" : CONFIG.categoryIcons[category] || "✨"}</span>${label}`;
  button.dataset.category = category;
  return button;
}

function getFilteredPlans() {
  const query = normalizeText(searchInput.value.trim());

  return PLANS.filter((plan) => {
    const matchesCategory = activeCategory === "all" || plan.category === activeCategory;
    const searchable = normalizeText(`${plan.title} ${plan.category} ${plan.description}`);
    return matchesCategory && (!query || searchable.includes(query));
  });
}

function getPlanAsset(plan, index = 0) {
  const categoryAsset = CONFIG.categoryAssets[plan.category] || "grogu";
  const rotation = ["grogu", "shrekOne", "shrekTwo", "jengi", "turtle"];
  return index % 4 === 0 ? rotation[index % rotation.length] : categoryAsset;
}

function renderPlans() {
  const filteredPlans = getFilteredPlans();
  plansGrid.replaceChildren();

  resultCount.textContent = `${filteredPlans.length} plan${filteredPlans.length === 1 ? "" : "es"} disponible${filteredPlans.length === 1 ? "" : "s"}`;

  if (!filteredPlans.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state glass-panel";
    empty.innerHTML = "<strong>No encontré ese plan</strong><span>Prueba con otra palabra o vuelve a ver todos.</span>";
    plansGrid.append(empty);
    return;
  }

  filteredPlans.forEach((plan, index) => {
    const card = document.createElement("article");
    card.className = "plan-card";
    card.dataset.planId = plan.id;
    card.dataset.category = CONFIG.categoryVisuals[plan.category]?.slug || "random";
    card.style.animationDelay = `${Math.min(index * 38, 520)}ms`;

    const shine = document.createElement("span");
    shine.className = "card-shine";

    const media = document.createElement("div");
    media.className = "plan-media";
    media.append(createCategoryVisual(plan.category, plan.title));
    setCategorySticker(media, getPlanAsset(plan, index), plan.category);

    const body = document.createElement("div");
    body.className = "plan-body";

    const number = document.createElement("span");
    number.className = "plan-number";
    number.textContent = String(PLANS.findIndex((item) => item.id === plan.id) + 1).padStart(2, "0");

    const category = document.createElement("span");
    category.className = "plan-category";
    category.textContent = `${CONFIG.categoryIcons[plan.category] || "✨"} ${plan.category}`;

    const title = document.createElement("h3");
    title.className = "plan-title";
    title.textContent = plan.title;

    const description = document.createElement("p");
    description.className = "plan-description";
    description.textContent = plan.description;

    const button = document.createElement("button");
    button.className = "card-btn";
    button.type = "button";
    button.textContent = "Elegir este";
    button.addEventListener("click", () => openPlanDetail(plan));

    card.addEventListener("click", (event) => {
      if (event.target.closest("button")) return;
      openPlanDetail(plan);
    });

    body.append(number, category, title, description, button);
    card.append(shine, media, body);
    attachTilt(card);
    plansGrid.append(card);
  });
}

function attachTilt(card) {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion) return;

  card.addEventListener("pointermove", (event) => {
    const rect = card.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    card.style.setProperty("--tilt-x", `${(-y * 5).toFixed(2)}deg`);
    card.style.setProperty("--tilt-y", `${(x * 6).toFixed(2)}deg`);
    card.style.setProperty("--shine-x", `${event.clientX - rect.left}px`);
    card.style.setProperty("--shine-y", `${event.clientY - rect.top}px`);
  });

  card.addEventListener("pointerleave", () => {
    card.style.setProperty("--tilt-x", "0deg");
    card.style.setProperty("--tilt-y", "0deg");
  });
}

function updateActiveCategory(category) {
  activeCategory = category;
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.classList.toggle("is-active", chip.dataset.category === category);
  });
  renderPlans();
}

function openPlanDetail(plan) {
  playEffect("select");
  burstAtCenter("select");
  vibrateSoft(12);
  selectedPlan = plan;
  detailTitle.textContent = plan.title;
  detailCategory.textContent = plan.category;
  detailDescription.textContent = plan.description;
  detailMeta.innerHTML = `
    <span>Elegido del catálogo</span>
    <strong>${CONFIG.detailHints[plan.category] || "Un plan especial para convertirlo en recuerdo."}</strong>
  `;
  dateInput.value = "";
  commentInput.value = "";
  dateInput.min = new Date().toISOString().split("T")[0];
  detailImage.dataset.category = CONFIG.categoryVisuals[plan.category]?.slug || "random";
  detailImage.replaceChildren(createCategoryVisual(plan.category, plan.title));
  setCategorySticker(detailImage, CONFIG.categoryAssets[plan.category] || "grogu", plan.title);
  showScreen("detail-screen");
}

function pickRandomPlan() {
  if (!PLANS.length || surpriseButton.disabled) return;

  playEffect("surprise");
  vibrateSoft([12, 35, 18]);
  document.body.classList.add("is-casting-surprise");
  window.setTimeout(() => document.body.classList.remove("is-casting-surprise"), 1900);
  const visibleCards = Array.from(document.querySelectorAll(".plan-card"));
  const candidatePlans = getFilteredPlans();
  if (!candidatePlans.length) {
    showToast("No hay planes visibles para sorprenderte.");
    return;
  }
  let ticks = 0;
  const randomPlan = candidatePlans[Math.floor(Math.random() * candidatePlans.length)];

  surpriseButton.disabled = true;
  surpriseButton.classList.add("is-spinning");
  surpriseButton.querySelector("span").textContent = "Buscando magia...";

  const animation = window.setInterval(() => {
    visibleCards.forEach((card) => card.classList.remove("is-surprise"));
    const activeCard = visibleCards[ticks % Math.max(visibleCards.length, 1)];
    if (activeCard) activeCard.classList.add("is-surprise");
    ticks += 1;
  }, 95);

  window.setTimeout(() => {
    window.clearInterval(animation);
    visibleCards.forEach((card) => card.classList.remove("is-surprise"));
    surpriseButton.disabled = false;
    surpriseButton.classList.remove("is-spinning");
    surpriseButton.querySelector("span").textContent = "Sorpréndeme";
    showToast(`La magia eligió este plan: ${randomPlan.title}`);
    burstAtCenter("surprise");
    openPlanDetail(randomPlan);
  }, 1700);
}

function prepareConfirmation() {
  if (!selectedPlan) {
    showToast("Primero elige un plan.");
    return;
  }

  if (!dateInput.value) {
    showToast("Elige una fecha para poder preparar el plan.");
    dateInput.focus();
    vibrateSoft(18);
    return;
  }

  const dateValue = dateInput.value || "Sin fecha elegida todavía";
  const commentValue = commentInput.value.trim() || "Sin comentario adicional";

  confirmationSummary.innerHTML = `
    <span>${selectedPlan.category}</span>
    <strong>${selectedPlan.title}</strong>
    <p>${selectedPlan.description}</p>
    <dl>
      <div><dt>Fecha</dt><dd>${dateValue}</dd></div>
      <div><dt>Comentario</dt><dd>${commentValue}</dd></div>
    </dl>
  `;

  showScreen("confirm-screen");
  updateWhatsappLink();
  vibrateSoft([14, 28, 14]);
  burstCelebration();
}

function getCleanWhatsappNumber() {
  return WHATSAPP_NUMBER.replace(/\D/g, "");
}

function buildWhatsappMessage() {
  if (!selectedPlan) return "";

  const dateValue = dateInput.value;
  const commentValue = commentInput.value.trim() || "Sin comentario adicional";
  return [
    "Elegí este plan 💌",
    "",
    `Plan: ${selectedPlan.title}`,
    `Categoría: ${selectedPlan.category}`,
    `Fecha sugerida: ${dateValue}`,
    `Comentario: ${commentValue}`,
    "",
    "Ahora tú te encargas del resto ✨"
  ].join("\n");
}

function buildWhatsappUrl() {
  const cleanNumber = getCleanWhatsappNumber();
  const message = buildWhatsappMessage();

  if (!cleanNumber || cleanNumber.length < 9) return "";
  if (!message) return "";

  return `https://api.whatsapp.com/send?phone=${cleanNumber}&text=${encodeURIComponent(message)}`;
}

function updateWhatsappLink() {
  if (!whatsappLink) return;

  const url = buildWhatsappUrl();

  if (!url) {
    whatsappLink.setAttribute("href", "#");
    whatsappLink.setAttribute("aria-disabled", "true");
    whatsappLink.classList.add("is-disabled");
    return;
  }

  whatsappLink.setAttribute("href", url);
  whatsappLink.removeAttribute("aria-disabled");
  whatsappLink.classList.remove("is-disabled");

  if (DEBUG_WHATSAPP) console.log("WhatsApp URL:", url);
}

function validateWhatsappReady() {
  if (!selectedPlan) {
    showToast("Primero elige un plan.");
    return false;
  }

  if (!dateInput.value) {
    showToast("Elige una fecha antes de abrir WhatsApp.");
    showScreen("detail-screen");
    dateInput.focus();
    return false;
  }

  const cleanNumber = getCleanWhatsappNumber();
  if (!cleanNumber || cleanNumber.length < 9) {
    showToast("El número de WhatsApp no está configurado correctamente.");
    return false;
  }

  return true;
}

function handleWhatsappClick(event) {
  if (!selectedPlan) {
    event.preventDefault();
    showToast("Primero elige un plan.");
    return;
  }

  if (!dateInput.value) {
    event.preventDefault();
    showToast("Elige una fecha antes de abrir WhatsApp.");
    return;
  }

  const cleanNumber = getCleanWhatsappNumber();
  if (!cleanNumber || cleanNumber.length < 9) {
    event.preventDefault();
    showToast("El número de WhatsApp no está configurado correctamente.");
    return;
  }

  const url = buildWhatsappUrl();
  if (!url) {
    event.preventDefault();
    showToast("No se pudo preparar el mensaje de WhatsApp.");
    return;
  }

  whatsappLink.href = url;
  playEffect("confirm");
  // Let the browser follow the real anchor href from the user's tap.
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.setTimeout(() => {
    toast.classList.remove("is-visible");
  }, 2600);
}

async function copyWhatsappMessage() {
  const message = buildWhatsappMessage();

  if (!message) {
    showToast("Primero elige un plan.");
    return;
  }

  try {
    await navigator.clipboard.writeText(message);
    showToast("Mensaje copiado. Ahora puedes pegarlo en WhatsApp.");
    playEffect("select");
    return;
  } catch (error) {
    showToast("No se pudo copiar automáticamente. Intenta manualmente.");
  }
}

function burstCelebration() {
  const card = document.querySelector(".confirmation-card");
  if (!card) return;

  for (let index = 0; index < 18; index += 1) {
    const spark = document.createElement("span");
    spark.className = "celebration-spark";
    spark.style.setProperty("--spark-x", `${Math.random() * 100}%`);
    spark.style.setProperty("--spark-delay", `${Math.random() * 0.4}s`);
    card.append(spark);
    window.setTimeout(() => spark.remove(), 1800);
  }
}

function burstAtCenter(type = "spark") {
  const count = type === "surprise" ? 22 : 12;
  for (let index = 0; index < count; index += 1) {
    const spark = document.createElement("span");
    spark.className = `screen-spark screen-spark-${type}`;
    spark.style.setProperty("--spark-left", `${42 + Math.random() * 16}%`);
    spark.style.setProperty("--spark-top", `${38 + Math.random() * 20}%`);
    spark.style.setProperty("--spark-dx", `${-90 + Math.random() * 180}px`);
    spark.style.setProperty("--spark-dy", `${-120 + Math.random() * 80}px`);
    document.body.append(spark);
    window.setTimeout(() => spark.remove(), 1200);
  }
}

function vibrateSoft(pattern) {
  if ("vibrate" in navigator) navigator.vibrate(pattern);
}

function setupButtonRipples() {
  document.querySelectorAll("button").forEach((button) => {
    button.addEventListener("pointerdown", (event) => {
      const rect = button.getBoundingClientRect();
      const ripple = document.createElement("span");
      ripple.className = "btn-ripple";
      ripple.style.left = `${event.clientX - rect.left}px`;
      ripple.style.top = `${event.clientY - rect.top}px`;
      button.append(ripple);
      window.setTimeout(() => ripple.remove(), 650);
    });
  });
}

function bindEvents() {
  document.querySelectorAll("[data-go]").forEach((button) => {
    button.addEventListener("click", () => {
      navigateTo(button.dataset.go, { intro: button.dataset.introTrigger === "true" });
    });
  });

  audioToggle.addEventListener("click", () => setAudioMuted(!isAudioMuted));

  categoryFilter.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    updateActiveCategory(button.dataset.category);
  });

  searchInput.addEventListener("input", renderPlans);
  showAllButton.addEventListener("click", () => {
    searchInput.value = "";
    updateActiveCategory("all");
  });

  surpriseButton.addEventListener("click", pickRandomPlan);
  prepareConfirmationButton.addEventListener("click", prepareConfirmation);
  whatsappLink.addEventListener("click", handleWhatsappClick);
  copyMessageButton.addEventListener("click", copyWhatsappMessage);
  setupButtonRipples();
}

function init() {
  letterText.textContent = CONFIG.letter;
  setupParticles();
  setupMagicCanvas();
  setupParallax();
  setupAssetStickers();
  renderCategories();
  renderPlans();
  bindEvents();
}

init();
