const WHATSAPP_NUMBER = "TU_NUMERO";

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
    description: "Películas, snacks, comodidad y pasarla bonito sin complicarnos.",
    image: "assets/shrek/shrek-01.png"
  },
  {
    id: "ir-al-cine",
    title: "Ir al cine",
    category: "Cine y películas",
    description: "Puede ser cine tradicional, cine en la playa o cine 4D.",
    image: "assets/monsters-inc/sully-01.png"
  },
  {
    id: "discoteca",
    title: "Discoteca",
    category: "Noche, música y baile",
    description: "Salir a bailar, despejarnos y vivir una noche diferente.",
    image: "assets/minions/minion-01.png"
  },
  {
    id: "hacer-un-viaje",
    title: "Hacer un viaje",
    category: "Aventura",
    description: "Una escapada para cambiar de aire y crear un recuerdo grande.",
    image: "assets/grogu/grogu-01.png"
  },
  {
    id: "salir-a-comer",
    title: "Salir a comer",
    category: "Comida y antojos",
    description: "Puede ser comer algo nuevo, una salida normal o que uno decida qué come el otro.",
    image: "assets/orchids/orchid-01.png"
  },
  {
    id: "caminar-sin-rumbo",
    title: "Caminar sin rumbo",
    category: "Para quedarnos tranquis",
    description: "Salir sin destino fijo y dejar que el momento decida.",
    image: "assets/shrek/fiona-01.png"
  },
  {
    id: "ir-a-tomar-unos-tragos",
    title: "Ir a tomar unos tragos",
    category: "Noche, música y baile",
    description: "Una salida relajada para conversar, brindar y pasarla bien.",
    image: "assets/minions/minion-02.png"
  },
  {
    id: "modo-relax",
    title: "Modo relax",
    category: "Para quedarnos tranquis",
    description: "Sauna, masajes o un plan para desconectarnos de todo.",
    image: "assets/grogu/grogu-02.png"
  },
  {
    id: "ir-a-los-juegos",
    title: "Ir a los juegos",
    category: "Diversión y juegos",
    description: "Juegos mecánicos, Coney Park, juegos inflables o algo parecido.",
    image: "assets/monsters-inc/mike-01.png"
  },
  {
    id: "patinaje-sobre-hielo",
    title: "Patinaje sobre hielo",
    category: "Diversión y juegos",
    description: "Un plan diferente, divertido y con posibles caídas memorables.",
    image: "assets/shrek/donkey-01.png"
  },
  {
    id: "bowling",
    title: "Bowling",
    category: "Diversión y juegos",
    description: "Competencia amistosa, risas y una excusa para molestarnos jugando.",
    image: "assets/minions/minion-03.png"
  },
  {
    id: "pintar-y-manualidades",
    title: "Pintar y manualidades",
    category: "Arte y experiencias",
    description: "Hacer algo creativo y llevarnos un recuerdo hecho por nosotros.",
    image: "assets/orchids/orchid-02.png"
  },
  {
    id: "cocinar-un-postre",
    title: "Cocinar un postre",
    category: "Comida y antojos",
    description: "Preparar algo dulce juntos, aunque salga perfecto o sea un desastre bonito.",
    image: "assets/grogu/grogu-03.png"
  },
  {
    id: "ir-a-la-playa-para-ver-el-atardecer",
    title: "Ir a la playa para ver el atardecer",
    category: "Aventura",
    description: "Ir a la playa, ver el cielo cambiar de color y quedarnos un rato ahí.",
    image: "assets/backgrounds/sunset-01.png"
  },
  {
    id: "hacer-un-en-vivo",
    title: "Hacer un en vivo",
    category: "Planes random especiales",
    description: "Hacer un live juntos, improvisar y ver qué pasa.",
    image: "assets/minions/minion-04.png"
  },
  {
    id: "ir-a-un-concierto",
    title: "Ir a un concierto",
    category: "Noche, música y baile",
    description: "Música en vivo, emoción y una noche para recordar.",
    image: "assets/monsters-inc/boo-01.png"
  },
  {
    id: "ir-a-un-stand-up",
    title: "Ir a un stand up",
    category: "Arte y experiencias",
    description: "Reírnos juntos y salir con frases internas nuevas.",
    image: "assets/shrek/puss-01.png"
  },
  {
    id: "plan-webing",
    title: "Plan webing",
    category: "Para quedarnos tranquis",
    description: "Simplemente existir juntos, sin presión, sin agenda y sin hacer mucho.",
    image: "assets/grogu/grogu-04.png"
  },
  {
    id: "ir-a-un-karaoke",
    title: "Ir a un karaoke",
    category: "Noche, música y baile",
    description: "Cantar bien, cantar mal o simplemente hacer show.",
    image: "assets/minions/minion-05.png"
  },
  {
    id: "ir-a-ver-lucha-libre",
    title: "Ir a ver lucha libre",
    category: "Planes random especiales",
    description: "Un plan intenso, raro y probablemente muy entretenido.",
    image: "assets/shrek/shrek-02.png"
  },
  {
    id: "carrera-en-karts",
    title: "Carrera en karts",
    category: "Diversión y juegos",
    description: "Competir, acelerar y ver quién maneja mejor.",
    image: "assets/monsters-inc/mike-02.png"
  },
  {
    id: "ir-a-un-game-center",
    title: "Ir a un game center",
    category: "Diversión y juegos",
    description: "Ir a un lugar con videojuegos, maquinitas y retos random.",
    image: "assets/minions/minion-06.png"
  },
  {
    id: "hacer-parapente",
    title: "Hacer parapente",
    category: "Aventura",
    description: "Un plan extremo para ver todo desde arriba y recordar ese momento siempre.",
    image: "assets/grogu/grogu-05.png"
  },
  {
    id: "ir-al-barrio-chino",
    title: "Ir al barrio chino",
    category: "Comida y antojos",
    description: "Comer, caminar, probar cosas y descubrir lugares.",
    image: "assets/orchids/orchid-03.png"
  },
  {
    id: "jugar-tenis",
    title: "Jugar tenis",
    category: "Diversión y juegos",
    description: "Un plan activo para jugar, competir y divertirnos.",
    image: "assets/shrek/fiona-02.png"
  },
  {
    id: "ir-a-lugares-pinterest",
    title: "Ir a lugares Pinterest",
    category: "Fotos y lugares bonitos",
    description: "Ir a lugares instagrameables para tomarnos fotos bonitas.",
    image: "assets/orchids/orchid-04.png"
  },
  {
    id: "ir-a-bailar",
    title: "Ir a bailar",
    category: "Noche, música y baile",
    description: "Salir a movernos, reírnos y olvidarnos del resto.",
    image: "assets/minions/minion-07.png"
  },
  {
    id: "ir-al-billar",
    title: "Ir al billar",
    category: "Diversión y juegos",
    description: "Una salida tranquila, competitiva y con buena conversación.",
    image: "assets/monsters-inc/sully-02.png"
  },
  {
    id: "ir-a-un-escape-room",
    title: "Ir a un escape room",
    category: "Diversión y juegos",
    description: "Resolver pistas juntos y comprobar qué tan buen equipo somos.",
    image: "assets/shrek/donkey-02.png"
  },
  {
    id: "ver-videos-de-youtube-en-su-casa",
    title: "Ver videos de YouTube en su casa",
    category: "Para quedarnos tranquis",
    description: "Videos random, risas, comodidad y cero producción.",
    image: "assets/grogu/grogu-06.png"
  }
];

const screens = document.querySelectorAll(".screen");
const plansGrid = document.querySelector("#plans-grid");
const categoryFilter = document.querySelector("#category-filter");
const searchInput = document.querySelector("#plan-search");
const showAllButton = document.querySelector("#show-all-btn");
const surpriseButton = document.querySelector("#surprise-btn");
const resultCount = document.querySelector("#result-count");
const toast = document.querySelector("#toast");

const detailImage = document.querySelector("#detail-image");
const detailTitle = document.querySelector("#detail-title");
const detailCategory = document.querySelector("#detail-category");
const detailDescription = document.querySelector("#detail-description");
const dateInput = document.querySelector("#date-input");
const commentInput = document.querySelector("#comment-input");
const whatsappButton = document.querySelector("#whatsapp-btn");

let activeCategory = "all";
let selectedPlan = null;

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
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function createFallback(label) {
  const fallback = document.createElement("div");
  fallback.className = "image-fallback";
  fallback.textContent = label;
  return fallback;
}

function setImage(container, src, fallbackLabel) {
  container.replaceChildren();

  const img = document.createElement("img");
  img.src = src;
  img.alt = fallbackLabel;
  img.loading = "lazy";
  img.onerror = () => {
    container.replaceChildren(createFallback(fallbackLabel));
  };

  container.append(img);
}

function setupDecorativeImages() {
  document.querySelectorAll(".sticker").forEach((sticker) => {
    const src = sticker.dataset.image;
    const fallback = sticker.dataset.fallback || "Magia";
    setImage(sticker, src, fallback);
  });
}

function renderCategories() {
  const allButton = document.createElement("button");
  allButton.className = "chip is-active";
  allButton.type = "button";
  allButton.textContent = "Ver todos";
  allButton.dataset.category = "all";
  categoryFilter.append(allButton);

  CATEGORIES.forEach((category) => {
    const button = document.createElement("button");
    button.className = "chip";
    button.type = "button";
    button.textContent = category;
    button.dataset.category = category;
    categoryFilter.append(button);
  });
}

function getFilteredPlans() {
  const query = normalizeText(searchInput.value.trim());

  return PLANS.filter((plan) => {
    const matchesCategory = activeCategory === "all" || plan.category === activeCategory;
    const searchable = normalizeText(`${plan.title} ${plan.category} ${plan.description}`);
    const matchesSearch = !query || searchable.includes(query);
    return matchesCategory && matchesSearch;
  });
}

function renderPlans() {
  const filteredPlans = getFilteredPlans();
  plansGrid.replaceChildren();
  resultCount.textContent = `${filteredPlans.length} plan${filteredPlans.length === 1 ? "" : "es"} disponible${filteredPlans.length === 1 ? "" : "s"}`;

  filteredPlans.forEach((plan, index) => {
    const card = document.createElement("article");
    card.className = "plan-card";
    card.style.animationDelay = `${Math.min(index * 35, 420)}ms`;

    const media = document.createElement("div");
    media.className = "plan-media";
    setImage(media, plan.image, plan.title);

    const body = document.createElement("div");
    body.className = "plan-body";

    const category = document.createElement("span");
    category.className = "plan-category";
    category.textContent = plan.category;

    const title = document.createElement("h3");
    title.className = "plan-title";
    title.textContent = plan.title;

    const description = document.createElement("p");
    description.className = "plan-description";
    description.textContent = plan.description;

    const button = document.createElement("button");
    button.className = "secondary-btn";
    button.type = "button";
    button.textContent = "Elegir plan";
    button.addEventListener("click", () => openPlanDetail(plan));

    body.append(category, title, description, button);
    card.append(media, body);
    plansGrid.append(card);
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
  selectedPlan = plan;
  detailTitle.textContent = plan.title;
  detailCategory.textContent = plan.category;
  detailDescription.textContent = plan.description;
  dateInput.value = "";
  commentInput.value = "";
  setImage(detailImage, plan.image, plan.title);
  showScreen("detail-screen");
}

function pickRandomPlan() {
  if (!PLANS.length) return;

  const visibleCards = Array.from(document.querySelectorAll(".plan-card"));
  let ticks = 0;

  surpriseButton.disabled = true;
  surpriseButton.textContent = "Eligiendo...";

  const animation = window.setInterval(() => {
    visibleCards.forEach((card) => card.classList.remove("is-surprise"));
    const card = visibleCards[ticks % Math.max(visibleCards.length, 1)];
    if (card) card.classList.add("is-surprise");
    ticks += 1;
  }, 110);

  window.setTimeout(() => {
    window.clearInterval(animation);
    visibleCards.forEach((card) => card.classList.remove("is-surprise"));
    surpriseButton.disabled = false;
    surpriseButton.textContent = "Sorpréndeme";

    const randomIndex = Math.floor(Math.random() * PLANS.length);
    const randomPlan = PLANS[randomIndex];
    showToast(`La magia eligio: ${randomPlan.title}`);
    openPlanDetail(randomPlan);
  }, 1500);
}

function buildWhatsappUrl() {
  const dateValue = dateInput.value || "Sin fecha elegida todavia";
  const commentValue = commentInput.value.trim() || "Sin comentario adicional";
  const text = [
    `Elegí este plan: ${selectedPlan.title}`,
    `Categoría: ${selectedPlan.category}`,
    `Fecha sugerida: ${dateValue}`,
    `Comentario: ${commentValue}`
  ].join("\n");

  return `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(text)}`;
}

function confirmByWhatsapp() {
  if (!selectedPlan) {
    showToast("Primero elige un plan.");
    return;
  }

  if (!WHATSAPP_NUMBER || WHATSAPP_NUMBER === "TU_NUMERO") {
    showToast("Cambia WHATSAPP_NUMBER por tu numero antes de publicar.");
  }

  window.open(buildWhatsappUrl(), "_blank", "noopener,noreferrer");
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.setTimeout(() => {
    toast.classList.remove("is-visible");
  }, 2600);
}

document.querySelectorAll("[data-go]").forEach((button) => {
  button.addEventListener("click", () => showScreen(button.dataset.go));
});

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
whatsappButton.addEventListener("click", confirmByWhatsapp);

setupDecorativeImages();
renderCategories();
renderPlans();
