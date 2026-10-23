let RATINGS = [];
let documentId = 0;
let totalDocuments = 0;
let selectedFields = {};
let rating = null;
let dirty = false;
let currentRows = [];
let currentRecords = null;
let expandedRecordsHeight = 0;
let saved = false;

async function api(url, options = {}) {
    const response = await fetch(url, options);

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

function element(tag, className = "", text = "") {
    const node = document.createElement(tag);
    node.className = className;
    node.textContent = text;
    return node;
}

function isRatingComplete() {

    if (!rating?.rating) return false;
    const evalFields = new Map(
        (currentRecords.eval || []).map(field => [field.id, field])
    );

    for (const row of currentRows) {
        if (!row.selected) continue;
        const fieldRating = rating.fields[row.id];
        if (!fieldRating?.rating) return false;
        if (row.eval === null) continue;
        const field = evalFields.get(row.eval);
        for (const subfield of field.subfields || []) {
            if (!selectedFields[field.tag]?.includes(subfield.code)) continue;
            if (!fieldRating.subfields?.[String(subfield.id)]) {
                return false;
            }
        }
    }
    return true;
}

function ratingGroup(name, value, onChange, className = "") {
    const group = element("div", `rating-group ${className}`);

    for (const rating of RATINGS) {
        const label = document.createElement("label");
        const input = document.createElement("input");

        input.type = "radio";
        input.name = name;
        input.value = rating;
        input.checked = value === rating;

        input.addEventListener("change", () => {
            onChange(rating);
            markDirty();
            updateNavigation();
        });

        label.append(input, document.createTextNode(rating.charAt(0).toUpperCase() + rating.slice(1)));
        group.append(label);
    }

    return group;
}

function markDirty() {
    dirty = true;
    saved = false;
}

function updateImageColumnHeight() {
    const images = document.querySelector(".images-column");
    images.style.maxHeight = `${expandedRecordsHeight}px`;
}

function measureExpandedRecordsHeight() {
    const records = document.getElementById("records");
    const collapsed = [...records.querySelectorAll(".subfield-hidden")];

    for (const cell of collapsed) {
        cell.classList.remove("subfield-hidden");
    }

    expandedRecordsHeight = records.getBoundingClientRect().height;

    for (const cell of collapsed) {
        cell.classList.add("subfield-hidden");
    }

    updateImageColumnHeight();
}

function toggleField(fieldId) {

    const cells = document.querySelectorAll(`[data-field="${fieldId}"]`);
    const toggle = cells[0].querySelector(".field-toggle");
    const collapsed = toggle.textContent === "▼";
    for (const cell of cells) {
        if (cell.classList.contains("subfield-cell")) {
            cell.classList.toggle("subfield-hidden", collapsed);
        }
    }
    toggle.textContent = collapsed ? "▶" : "▼";
    toggle.title = collapsed ? "Expand field" : "Collapse field";
}

function renderMissingField(row, fieldId, collapsible) {

    const container = element("div", "field field-empty field-main");
    container.dataset.field = fieldId;

    const header = element("div", "field-header");
    if (collapsible) {
        const toggle = element("button", "field-toggle", "▼");
        toggle.type = "button";
        toggle.title = "Collapse field";
        toggle.addEventListener("click", () => toggleField(fieldId));
        header.append(toggle);
    } else {
        header.append(element("span", "field-toggle-spacer"));
    }
    header.append(element("span", "tag", row.tag));

    if (row.selected) {
        const id = row.id;
        const fieldRating = rating.fields[id] || { rating: null, subfields: {} };

        header.append(ratingGroup(`field-${id}`, fieldRating.rating, value => {
            rating.fields[id] = { rating: value, subfields: {} };
        }, "field-rating"));
    }

    container.append(header);
    return container;
}

function renderField(field, editable, fieldId, collapsible) {

    const container = element("div", "field field-main");
    container.dataset.field = fieldId;

    const header = element("div", "field-header");

    if (editable && collapsible) {
        const toggle = element("button", "field-toggle", "▼");
        toggle.type = "button";
        toggle.title = "Collapse field";
        toggle.addEventListener("click", () => toggleField(fieldId));
        header.append(toggle);
    } else {
        header.append(element("span", "field-toggle-spacer"));
    }

    header.append(element("span", "tag", field.tag));

    if (field.ind1 !== undefined) {
        const ind1 = field.ind1?.trim() || "#";
        const ind2 = field.ind2?.trim() || "#";
        header.append(element("span", "indicators", `${ind1}${ind2}`));
    }

    const selected = editable && Object.hasOwn(selectedFields, field.tag);

    if (selected) {
        const id = String(field.id);
        const fieldRating = rating.fields[id] || { rating: null, subfields: {} };

        header.append(ratingGroup(`field-${id}`, fieldRating.rating, value => {
            if (!rating.fields[id]) {
                rating.fields[id] = { rating: null, subfields: {} };
            }

            const fieldRating = rating.fields[id];
            fieldRating.rating = value;

            const subfields = (field.subfields || []).filter(subfield =>
                selectedFields[field.tag].includes(subfield.code)
            );

            const anyRated = subfields.some(subfield =>
                fieldRating.subfields?.[String(subfield.id)] != null
            );

            if (!anyRated) {
                fieldRating.subfields ||= {};

                for (const subfield of subfields) {
                    fieldRating.subfields[String(subfield.id)] = value;
                }

                for (const subfield of subfields) {
                    const name = `subfield-${id}-${subfield.id}`;
                    const input = document.querySelector(`input[name="${name}"][value="${value}"]`);

                    if (input) input.checked = true;
                }
            }
        }, "field-rating"));
    }

    container.append(header);
    return container;
}

function renderSubfield(field, subfield, editable, rowId) {

    const container = element("div", "field subfield-cell");
    container.dataset.field = rowId;

    if (!subfield) {
        container.classList.add("subfield-empty");
        return container;
    }

    const content = element("div", "subfield");
    content.append(element("span", "code", `$${subfield.code}`));
    content.append(document.createTextNode(subfield.value));
    container.append(content);

    const selected = editable && Object.hasOwn(selectedFields, field.tag);

    if (selected && selectedFields[field.tag].includes(subfield.code)) {
        const fieldId = String(field.id);
        const subfieldId = String(subfield.id);
        const value = rating.fields[fieldId]?.subfields?.[subfieldId] || null;

        container.append(ratingGroup(`subfield-${fieldId}-${subfieldId}`, value, value => {
            if (!rating.fields[fieldId]) {
                rating.fields[fieldId] = { rating: null, subfields: {} };
            }
            rating.fields[fieldId].subfields[subfieldId] = value;
        }, "subfield-rating"));
    }

    return container;
}

function renderRecords(records, rows) {

    const container = document.getElementById("records");
    container.replaceChildren();

    const names = ["eval", "gold", "platinum"].filter(name => records[name]);
    container.style.setProperty("--columns", names.length);

    document.querySelector(".document-content").style.setProperty("--record-columns", names.length);

    const lookup = {};

    for (const name of names) {
        lookup[name] = new Map(records[name].map(field => [field.id, field]));
    }

    for (const name of names) {
        container.append(element("h2", "record-title", name.toUpperCase()));
    }

    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];

        const fields = names.map(name =>
            row[name] !== null ? lookup[name].get(row[name]) : null
        );

        const fieldId = String(i);
        const collapsible = fields.some(field => (field?.subfields?.length || 0) > 0);

        // Field header row
        for (let j = 0; j < names.length; j++) {
            const field = fields[j];

            if (field) {
                container.append(renderField(field, names[j] === "eval", fieldId, collapsible));
            } else if (names[j] === "eval") {
                container.append(renderMissingField(row, fieldId, collapsible));
            } else {
                const empty = element("div", "field field-empty field-main");
                empty.dataset.field = fieldId;
                container.append(empty);
            }
        }

        // Preserve exact subfield alignment by code and occurrence.
        const codes = new Set();

        for (const field of fields) {
            for (const subfield of field?.subfields || []) {
                codes.add(subfield.code);
            }
        }

        const groupedSubfields = fields.map(field => groupSubfields(field));

        for (const code of [...codes].sort()) {
            const maxCount = Math.max(...groupedSubfields.map(group => (group[code] || []).length));

            for (let k = 0; k < maxCount; k++) {
                for (let j = 0; j < names.length; j++) {
                    const subfield = groupedSubfields[j][code]?.[k] || null;
                    container.append(renderSubfield(fields[j], subfield, names[j] === "eval", fieldId));
                }
            }
        }
    }
}

function groupSubfields(field) {
    const grouped = {};

    for (const subfield of field?.subfields || []) {
        if (!grouped[subfield.code]) {
            grouped[subfield.code] = [];
        }

        grouped[subfield.code].push(subfield);
    }

    return grouped;
}

function renderImages(images) {
    const container = document.getElementById("images");
    container.replaceChildren();

    for (const url of images) {
        const link = document.createElement("a");
        link.href = url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";

        const image = document.createElement("img");
        image.src = url;
        image.alt = "Document image";
        image.loading = "lazy";

        link.append(image);
        container.append(link);
    }
}

function renderDocument(data) {
    
    rating = structuredClone(data.rating);
    rating.fields ||= {};
    currentRows = data.rows;

    const ratingContainer = document.getElementById("document-rating");
    ratingContainer.replaceChildren();

    ratingContainer.append(ratingGroup("document-rating", rating.rating, value => {
        rating.rating = value;
        updateNavigation();
    }));

    currentRecords = data.records;

    renderImages(data.images);
    renderRecords(currentRecords, currentRows);

    requestAnimationFrame(() => {
        measureExpandedRecordsHeight();
    });

    dirty = false;
    saved = false;
}

async function loadDocument(id) {
    const data = await api(`/api/documents/${id}`);

    documentId = id;
    renderDocument(data);
    updateNavigation();
    window.scrollTo(0, 0);
}

function updateNavigation() {
    document.getElementById("progress").textContent = `${documentId + 1} / ${totalDocuments}`;
    document.getElementById("previous").disabled = documentId === 0;

    const button = document.getElementById("save-next");
    const last = documentId === totalDocuments - 1;

    button.textContent = last ? (saved ? "Saved ✓" : "Save") : "Save →";
    button.disabled = !isRatingComplete() || saved;
}

async function saveDocument() {
    if (!isRatingComplete()) return false;

    await api(`/api/documents/${documentId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            rating: rating.rating,
            fields: rating.fields
        })
    });

    dirty = false;
    saved = documentId === totalDocuments - 1;
    updateNavigation();
    return true;
}

async function navigate(direction) {
    if (dirty && !confirm("You have unsaved changes. Continue without saving?")) {
        return;
    }

    await loadDocument(documentId + direction);
}

document.getElementById("previous").addEventListener("click", () => navigate(-1));
document.getElementById("save-next").addEventListener("click", async () => {
    try {
        const saved = await saveDocument();

        if (saved && documentId < totalDocuments - 1) {
            await loadDocument(documentId + 1);
        }
    } catch (error) {
        alert(error.message);
    }
});

window.addEventListener("beforeunload", event => {
    if (dirty) {
        event.preventDefault();
        event.returnValue = "";
    }
});

async function init() {
    try {
        const session = await api("/api/session");
        totalDocuments = session.total;
        RATINGS = session.ratings;
        selectedFields = session.selected_fields;
        await loadDocument(session.initial_document);
    } catch (error) {
        alert(error.message);
    }
}

document.addEventListener("keydown", event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;

    const target = event.target;
    if (target instanceof HTMLElement && target.closest("input, textarea, select, [contenteditable]")) return;

    if (event.key === "ArrowLeft") {
        const button = document.getElementById("previous");
        if (!button.disabled) {
            event.preventDefault();
            button.click();
        }
    }

    if (event.key === "ArrowRight") {
        const button = document.getElementById("save-next");
        if (!button.disabled) {
            event.preventDefault();
            button.click();
        }
    }
});

window.addEventListener("resize", () => {
    requestAnimationFrame(measureExpandedRecordsHeight);
});

init();