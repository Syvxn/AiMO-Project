from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "grade5_english_textbook.pdf"

units = [
    {
        "title": "The Secret Garden Map",
        "topic": "setting, sequence, and precise nouns",
        "passage": "Maya discovered a folded map beneath a loose floorboard in her grandmother's attic. The map showed a garden that no longer appeared on any modern street. A silver path wound past a pond, a stone bench, and an old pear tree. At the bottom, someone had written, 'Look closely at what the seasons hide.' Maya packed a notebook and a pencil before leaving the house.",
        "vocabulary": "attic: a room beneath a roof; modern: belonging to the present time; wound: curved or twisted; seasons: parts of the year with different weather; discovered: found something unexpectedly.",
        "grammar": "A precise noun names a person, place, thing, or idea clearly. Replace a general noun with a precise noun: place becomes garden, tree becomes pear tree, and thing becomes map. Sequence words such as first, next, then, and finally show the order of events.",
        "questions": ["Where did Maya find the map?", "What landmarks were shown on it?", "What did Maya pack?", "Why is the phrase 'Look closely' an important clue?"],
        "writing": "Write five sentences describing a mysterious place. Use at least three precise nouns and three sequence words.",
    },
    {
        "title": "A River That Remembers",
        "topic": "main idea, details, and water conservation",
        "passage": "The Willow River begins in a forested hill and travels through farms, towns, and wetlands before reaching the sea. Many living things depend on it. Fish lay eggs in cool water, frogs hide among reeds, and people use the river to water crops. During a dry summer, the community measured its water carefully and planted native grasses along the banks. The grasses held soil in place and gave small animals shelter.",
        "vocabulary": "wetlands: places where land is covered by shallow water; depend: need something in order to live; reeds: tall grass-like plants that grow near water; native: naturally found in a particular place; shelter: a safe place for protection.",
        "grammar": "The main idea is the most important point in a passage. Supporting details explain, prove, or give examples of that point. A dependent clause cannot stand alone: because the river was low. An independent clause can stand alone: The community measured its water.",
        "questions": ["Where does the Willow River begin?", "Name two living things that depend on the river.", "Why did the community plant native grasses?", "What is the main idea of the passage?"],
        "writing": "Write a short paragraph explaining two ways a community can conserve water. Include one reason for each way.",
    },
    {
        "title": "The Clockmaker's Apprentice",
        "topic": "character traits, dialogue, and adverbs",
        "passage": "Jonah wanted to repair clocks, but he often rushed. His mentor, Mrs. Bell, gave him a quiet wooden clock with twelve tiny gears. 'A careful clockmaker listens before touching a tool,' she said. Jonah examined the gears patiently and noticed that one spring was bent. He straightened it gently, cleaned the dust, and waited. When the clock began to tick, Jonah smiled. He had learned that patience was not the same as doing nothing; it was doing each step well.",
        "vocabulary": "apprentice: a learner who works with an expert; mentor: a trusted teacher; gears: toothed wheels that work together; spring: a coiled piece of metal that stores energy; patiently: calmly while waiting.",
        "grammar": "An adverb describes how, when, or where an action happens. In the sentence Jonah examined the gears patiently, patiently explains how he examined them. Dialogue is the exact speech of a character and is placed inside quotation marks.",
        "questions": ["What mistake did Jonah often make?", "Who was Mrs. Bell?", "What problem did Jonah discover?", "What lesson did Jonah learn?"],
        "writing": "Write a conversation between an expert and a beginner. Use quotation marks and at least four adverbs.",
    },
    {
        "title": "The Science of Sleep",
        "topic": "expository text, cause and effect, and health",
        "passage": "Sleep is an active time for the human body. While a person sleeps, the brain organizes memories, the body repairs cells, and muscles recover from daily activity. Light from a phone or tablet can make it harder for the brain to prepare for sleep. A regular bedtime, a dark room, and a quiet routine can help the body recognize that it is time to rest. Good sleep supports attention, learning, and a healthy immune system.",
        "vocabulary": "organizes: arranges in a useful order; memories: information stored from experiences; repairs: fixes damage; routine: a repeated pattern of actions; immune system: the body's defense against illness.",
        "grammar": "Expository writing explains a subject using facts. Cause tells why something happens, and effect tells what happens as a result. Words such as because, therefore, so, and as a result connect causes and effects.",
        "questions": ["What does the brain do during sleep?", "How can phone light affect sleep?", "List two habits that can help a person rest.", "What is one effect of good sleep?"],
        "writing": "Explain how one healthy habit causes a positive effect. Use because and as a result.",
    },
    {
        "title": "Letters from the Lighthouse",
        "topic": "historical fiction, point of view, and context clues",
        "passage": "In 1912, Eli lived with his aunt in a lighthouse on the northern coast. Each evening, he helped polish the large lens that sent a bright signal across the dark water. One stormy night, the wind roared like a train and waves struck the rocks below. Eli checked the oil, trimmed the wick, and watched the beam sweep across the sea. At dawn, a fishing boat appeared safely in the harbor. Eli's aunt hugged him and called his work essential.",
        "vocabulary": "lighthouse: a tower with a guiding light for ships; lens: curved glass that bends light; signal: a sign that communicates information; wick: a thread that burns in a lamp; essential: completely necessary.",
        "grammar": "Point of view tells who is telling a story. First person uses I or we. Third person uses he, she, they, or a character's name. Context clues are nearby words that help a reader infer an unfamiliar word's meaning.",
        "questions": ["When does Eli help polish the lens?", "What did Eli do during the storm?", "Why was his work essential?", "Which details show that the passage takes place in the past?"],
        "writing": "Rewrite the passage's storm scene from Eli's first-person point of view.",
    },
    {
        "title": "The Pollinator Patrol",
        "topic": "problem and solution, ecosystems, and subject-verb agreement",
        "passage": "A school garden was producing fewer tomatoes than usual. The students observed the garden and learned that bees and butterflies carried pollen from flower to flower. Without enough pollinators, many flowers could not develop into fruit. The class planted lavender, sunflowers, and native wildflowers around the garden. They also placed a shallow dish of water nearby. By the end of the season, more pollinators visited the garden and the tomato plants produced a larger crop.",
        "vocabulary": "pollinator: an animal that carries pollen between flowers; pollen: fine powder that helps plants reproduce; develop: grow or change into something; native: naturally belonging to a region; crop: plants grown for food.",
        "grammar": "The subject and verb must agree. A singular subject takes a singular verb: The bee carries pollen. A plural subject takes a plural verb: Bees carry pollen. Do not let words between the subject and verb confuse you.",
        "questions": ["What problem did the school garden have?", "Why are pollinators important?", "What solution did the students try?", "What evidence shows that the solution worked?"],
        "writing": "Describe an environmental problem and propose a solution. Include a clear problem, two actions, and an expected result.",
    },
    {
        "title": "The Bridge of Paper",
        "topic": "engineering design, measurement, and comparative adjectives",
        "passage": "The class challenge was simple: build a bridge from twenty sheets of paper that could hold a stack of books. The first team rolled the paper into tubes, but the tubes bent under pressure. The second team folded wide beams and connected them with triangular supports. Their bridge was stronger because triangles spread force across several sides. After testing, the students changed the distance between the supports and made the bridge even steadier.",
        "vocabulary": "challenge: a difficult task; pressure: force pushing against something; beam: a long piece that supports weight; triangular: shaped like a triangle; steadier: more stable and less likely to move.",
        "grammar": "Comparative adjectives compare two things: stronger, wider, and steadier. Superlative adjectives compare three or more things: strongest, widest, and steadiest. Use than after a comparative adjective when naming the second thing.",
        "questions": ["What materials could the students use?", "Why did the first team's tubes bend?", "How did triangular supports help?", "What change made the bridge steadier?"],
        "writing": "Describe a design you would test. Use at least five measurement or comparison words.",
    },
    {
        "title": "A Song for the Moon",
        "topic": "poetry, imagery, figurative language, and rhythm",
        "passage": "The moon is a lantern above the sleeping town. It spills silver on the rooftops and paints a quiet road across the lake. The night wind whispers through the pine trees, while stars glitter like grains of salt. I walk home slowly, carrying the sky's gentle music in my thoughts. When morning opens its golden eye, the moon fades, but its calm remains.",
        "vocabulary": "lantern: a portable light; rooftops: the outside surfaces of roofs; whispers: speaks very softly; glitter: shines with small flashes; imagery: language that creates a picture or sensation.",
        "grammar": "A metaphor compares two unlike things without using like or as: The moon is a lantern. A simile uses like or as: Stars glitter like grains of salt. Personification gives human actions to something nonhuman: the morning opens its eye.",
        "questions": ["What is the moon compared to?", "Which phrase is a simile?", "What sense does the imagery of silver rooftops appeal to?", "What feeling does the poem create?"],
        "writing": "Write an eight-line poem about weather. Include one metaphor, one simile, and one example of personification.",
    },
    {
        "title": "The Traveling Seed",
        "topic": "sequence, adaptation, and prefixes",
        "passage": "A maple seed begins its journey when the wind lifts its wing-shaped body from a branch. It spins through the air and may land beside a stream, under leaves, or on a patch of bare soil. If the seed receives water, warmth, and enough light, a root pushes downward. A small stem rises upward. Over time, the seedling grows leaves that collect sunlight and help the young tree make food.",
        "vocabulary": "journey: travel from one place to another; patch: a small area; receives: gets something; seedling: a young plant; collect: gather together.",
        "grammar": "A prefix is added to the beginning of a word and changes its meaning. Re- can mean again, as in regrow. Un- can mean not, as in unsafe. Pre- can mean before, as in preview. Use the sentence around a word to check whether the prefix meaning fits.",
        "questions": ["What carries the maple seed?", "Where might the seed land?", "What three things help the seed grow?", "What does the prefix re- mean in regrow?"],
        "writing": "Explain the life cycle of a plant in six ordered steps. Use first, next, then, after that, and finally.",
    },
    {
        "title": "The Fairness Committee",
        "topic": "opinion writing, evidence, and conjunctions",
        "passage": "The student council wanted to choose a new playground activity. Some students supported a garden because it would provide fresh vegetables and a place to learn about nature. Others preferred a shaded reading area because students needed a quiet place during recess. The committee surveyed every class, compared the results, and proposed building a small garden beside the reading area. Their plan respected both ideas and used the available space carefully.",
        "vocabulary": "council: a group that makes decisions; supported: agreed with or helped; proposed: suggested a plan; surveyed: asked people questions to gather information; respected: treated an idea as worthy of consideration.",
        "grammar": "An opinion states what someone thinks. Evidence supports an opinion with facts, examples, or information from a survey. Coordinating conjunctions join equal ideas: and adds, but contrasts, so shows a result, and or gives a choice.",
        "questions": ["What two activities did students suggest?", "How did the committee gather information?", "Why did the committee combine the ideas?", "Which detail is evidence rather than an opinion?"],
        "writing": "Write an opinion about an improvement your school could make. State your opinion, give two pieces of evidence, and end with a conclusion.",
    },
]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=28, leading=34, alignment=TA_CENTER, textColor=colors.HexColor("#17324d"), spaceAfter=18))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=14, leading=20, alignment=TA_CENTER, textColor=colors.HexColor("#49657a")))
styles.add(ParagraphStyle(name="Unit", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=colors.HexColor("#17324d"), spaceAfter=8))
styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#2b6f77"), spaceBefore=12, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyTextBook", parent=styles["BodyText"], fontSize=10.5, leading=16, spaceAfter=8, textColor=colors.HexColor("#22313f")))
styles.add(ParagraphStyle(name="SmallBook", parent=styles["BodyText"], fontSize=9, leading=13, textColor=colors.HexColor("#405565")))


def para(text, style="BodyTextBook"):
    return Paragraph(text.replace("&", "&amp;"), styles[style])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d5e1e5"))
    canvas.line(0.7 * inch, 0.55 * inch, 7.8 * inch, 0.55 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#607786"))
    canvas.drawString(0.7 * inch, 0.35 * inch, "Grade 5 English: Reading, Language, and Writing")
    canvas.drawRightString(7.8 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=LETTER, rightMargin=0.72 * inch, leftMargin=0.72 * inch, topMargin=0.72 * inch, bottomMargin=0.75 * inch, title="Grade 5 English: Reading, Language, and Writing", author="AiMO Project")
    story = [Spacer(1, 1.1 * inch), Paragraph("Grade 5 English", styles["CoverTitle"]), Paragraph("Reading, Language, and Writing", styles["CoverTitle"]), Spacer(1, 0.25 * inch), Paragraph("An original practice textbook for classroom learning and quiz generation", styles["CoverSub"]), Spacer(1, 0.6 * inch), para("This open practice book contains ten original units. Each unit includes a reading passage, vocabulary, language study, comprehension questions, and a writing task. The material is designed for students around fifth-grade level and for retrieval-based educational tools.", "CoverSub"), PageBreak(), Paragraph("Contents", styles["Unit"])]
    for index, unit in enumerate(units, 1):
        story.append(para(f"Unit {index}: {unit['title']} - {unit['topic']}", "BodyTextBook"))
    story.append(PageBreak())

    for index, unit in enumerate(units, 1):
        story.extend([Paragraph(f"Unit {index}: {unit['title']}", styles["Unit"]), para(f"Focus: {unit['topic']}", "SmallBook"), Paragraph("Reading Passage", styles["Section"]), para(unit["passage"]), Paragraph("Vocabulary", styles["Section"]), para(unit["vocabulary"]), Paragraph("Language Study", styles["Section"]), para(unit["grammar"]), Paragraph("Check Your Understanding", styles["Section"])])
        question_rows = [[Paragraph(f"{n}. {question}", styles["BodyTextBook"])] for n, question in enumerate(unit["questions"], 1)]
        table = Table(question_rows, colWidths=[6.9 * inch])
        table.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#b9ced2")), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5e1e5")), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3f8f8")), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story.extend([table, Paragraph("Writing Workshop", styles["Section"]), para(unit["writing"]), Spacer(1, 8), para(f"Unit {index} review: Explain the passage's main idea, define two vocabulary words, and write one new question about the text.", "SmallBook")])
        if index != len(units):
            story.append(PageBreak())
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
    print(OUTPUT)
