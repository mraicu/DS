const app = document.getElementById("app");
const page = document.body.dataset.page || "about";

function createSection(id, title, subtitle) {
  const section = document.createElement("section");
  section.className = "section";
  section.id = id;

  const header = document.createElement("div");
  header.className = "section-header";

  const heading = document.createElement("h2");
  heading.textContent = title;

  header.appendChild(heading);
  section.appendChild(header);

  if (subtitle){
    const sub = document.createElement("p");
    sub.className = "section-subtitle";
    sub.textContent = subtitle;
    header.appendChild(sub);
  }
  
  return section;
}

function createTag(text) {
  const tag = document.createElement("span");
  tag.className = "tag";
  tag.textContent = text;
  return tag;
}

function createCard(title, meta, details) {
  const card = document.createElement("article");
  card.className = "card";

  const h3 = document.createElement("h3");
  h3.textContent = title;

  const metaLine = document.createElement("p");
  metaLine.className = "card-meta";
  metaLine.textContent = meta;

  card.appendChild(h3);
  card.appendChild(metaLine);

  if (typeof details === "string" && details.trim().length) {
    const description = document.createElement("p");
    description.textContent = details;
    card.appendChild(description);
  } else if (Array.isArray(details) && details.length) {
    const list = document.createElement("ul");
    list.className = "card-list";
    details.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    card.appendChild(list);
  }

  return card;
}

function buildAboutSection(data) {
  const section = createSection(
    "about",
    "About Me",
    "A quick snapshot of who I am."
  );

  const layout = document.createElement("div");
  layout.className = "about-grid";

  const hero = document.createElement("div");
  hero.className = "hero-card";

  const name = document.createElement("h1");
  name.textContent = data.person.fullName;

  const role = document.createElement("p");
  role.className = "hero-role";
  role.textContent = data.person.role;

  const summary = document.createElement("p");
  summary.className = "hero-summary";
  summary.textContent = data.person.summary;

  const info = document.createElement("div");
  info.className = "info-grid";

  const dob = document.createElement("div");
  dob.className = "info-item";
  dob.innerHTML = `<span>Date of birth</span><strong>${data.person.dateOfBirth}</strong>`;

  const location = document.createElement("div");
  location.className = "info-item";
  location.innerHTML = `<span>Location</span><strong>${data.person.location}</strong>`;

  info.appendChild(dob);
  info.appendChild(location);

  const highlightWrap = document.createElement("div");
  highlightWrap.className = "tag-row";
  data.person.highlights.forEach((item) =>
    highlightWrap.appendChild(createTag(item))
  );

  hero.appendChild(name);
  hero.appendChild(role);
  hero.appendChild(summary);
  hero.appendChild(info);
  hero.appendChild(highlightWrap);

  const photo = document.createElement("div");
  photo.className = "profile-photo";
  const img = document.createElement("img");
  img.src = "image.jpg";
  img.alt = `${data.person.fullName} profile photo`;
  photo.appendChild(img);

  layout.appendChild(hero);
  layout.appendChild(photo);
  section.appendChild(layout);

  return section;
}

function buildCareerSection(data) {
  const section = createSection(
    "career",
    "Experience and Education",
  );

  const grid1 = document.createElement("div");
  grid1.className = "card-grid";

  data.education.forEach((item) => {
    grid1.appendChild(
      createCard(
        item.title,
        `${item.organization} - ${item.period}`,
        item.details
      )
    );
  });


  const grid2 = document.createElement("div");
  grid2.className = "card-grid";

  data.experience.forEach((item) => {
    grid2.appendChild(
      createCard(
        item.title,
        `${item.organization} - ${item.period}`,
        item.details
      )
    );
  });

  section.appendChild(grid2);
  section.appendChild(grid1);

  return section;
}

function buildHobbiesSection(data) {
  const section = createSection(
    "hobbies",
    "Hobbies and Passions",
    "Activities that keep me balanced."
  );

  const list = document.createElement("div");
  list.className = "hobby-grid";

  data.hobbies.forEach((item) => {
    const card = document.createElement("article");
    card.className = "hobby-card";

    const title = document.createElement("h3");
    title.textContent = item.title;

    const description = document.createElement("p");
    description.textContent = item.description;

    card.appendChild(title);
    card.appendChild(description);
    list.appendChild(card);
  });

  section.appendChild(list);
  return section;
}

if (page === "about") {
  app.appendChild(buildAboutSection(profileData));
} else if (page === "career") {
  app.appendChild(buildCareerSection(profileData));
} else if (page === "hobbies") {
  app.appendChild(buildHobbiesSection(profileData));
} else {
  app.appendChild(buildAboutSection(profileData));
}
