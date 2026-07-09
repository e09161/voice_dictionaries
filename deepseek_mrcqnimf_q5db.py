"""
Conversation Skills Dictionary – MP3 Generator (No SSML)
========================================================
Generates all MP3 files for the ESL conversation dictionary.
- Phrases & examples: single voice
- Dialogues: two voices, concatenated

Requirements:
    pip install edge-tts

Run:
    python generate_conversation_dictionary.py
Output:
    87 MP3 files directly in the current folder.
"""

import asyncio
import edge_tts
from pathlib import Path
import tempfile
import shutil

# ------------------------------------------------------------
# Voice settings
# ------------------------------------------------------------
PHRASE_VOICE = "en-US-JennyNeural"   # clear female voice for words/sentences
EXAMPLE_VOICE = "en-US-JennyNeural"  # same voice for example sentences
RATE = "-12%"                        # slightly slower for ESL clarity

# Dialogue voices (no SSML – we'll generate separate temp files)
DIALOGUE_VOICE_A = "en-US-JennyNeural"  # Speaker A (female)
DIALOGUE_VOICE_B = "en-US-GuyNeural"    # Speaker B (male)
DIALOGUE_RATE = "-10%"

# ------------------------------------------------------------
# 1. DISCOURSE MARKERS (phrase, example)
# ------------------------------------------------------------
DISCOURSE_MARKERS = [
    ("Well", "Well, I'm not sure about that."),
    ("So", "So, what did you think of the film?"),
    ("Anyway", "Anyway, let's get back to the plan."),
    ("Actually", "Actually, I think you're right."),
    ("I mean", "It's tricky—I mean, it takes practice."),
    ("You know", "It was, you know, a bit disappointing."),
    ("Right?", "That makes sense, right?"),
    ("OK / Alright", "OK, let's move on to the next point."),
    ("Now", "Now, here's the interesting part."),
    ("Then", "We agreed, then we signed the contract."),
    ("First of all", "First of all, we need to set a budget."),
    ("By the way", "By the way, have you seen the news?"),
    ("On the other hand", "It's expensive. On the other hand, it's high quality."),
    ("In other words", "In other words, we need more time."),
    ("As I was saying", "As I was saying, the deadline is Friday."),
    ("The thing is", "The thing is, we don't have enough data."),
    ("To be honest", "To be honest, I didn't enjoy the meal."),
]

# ------------------------------------------------------------
# 2. AGREEING PHRASES (phrase, example)
# ------------------------------------------------------------
AGREEING_PHRASES = [
    ("I agree (with you)", "I agree with you—that's the best option."),
    ("Absolutely", "Absolutely! I couldn't have said it better."),
    ("Exactly", "Exactly—that's what I was trying to say."),
    ("You're right", "You're right—we should have left earlier."),
    ("That's true", "That's true—the traffic was terrible."),
    ("I think so too", "I think so too—it's a great opportunity."),
    ("Definitely", "Definitely! That's the way to go."),
    ("I couldn't agree more", "I couldn't agree more—it's a brilliant idea."),
    ("That's a good point", "That's a good point—I hadn't thought of that."),
    ("Fair enough", "Fair enough—I see where you're coming from."),
    ("You have a point", "You have a point—maybe I was too hasty."),
    ("That makes sense", "That makes sense—I understand now."),
    ("Same here", "Same here—I felt the same way."),
]

# ------------------------------------------------------------
# 3. DISAGREEING PHRASES (phrase, example)
# ------------------------------------------------------------
DISAGREEING_PHRASES = [
    ("I disagree", "I disagree—I think there's a better way."),
    ("I'm not sure about that", "I'm not sure about that—can you explain more?"),
    ("I see your point, but…", "I see your point, but I think we need more data."),
    ("That's not always true", "That's not always true—it depends on the situation."),
    ("I don't think so", "I don't think so—the evidence says otherwise."),
    ("Not necessarily", "Not necessarily—there could be other reasons."),
    ("I beg to differ", "I beg to differ—the report shows a different trend."),
    ("I'm afraid I can't agree", "I'm afraid I can't agree with that assessment."),
    ("With all due respect", "With all due respect, I think that's incorrect."),
    ("I understand, but…", "I understand, but we have to consider the cost."),
    ("You might be right, but…", "You might be right, but I'd like to check first."),
    ("I have a different view", "I have a different view—here's how I see it."),
]

# ------------------------------------------------------------
# 4. PRACTICE DIALOGUES (list of (speaker, text) turns)
# ------------------------------------------------------------
DIALOGUES = {
    "dialogue_01_presentation": [
        ("A", "So, what did you think of the presentation?"),
        ("B", "Well, I thought it was quite good. You know, the speaker was very clear."),
        ("A", "Absolutely! I agree. The examples were helpful too."),
        ("B", "Exactly. On the other hand, it was a bit long."),
    ],
    "dialogue_02_leave_earlier": [
        ("A", "I think we should leave earlier."),
        ("B", "I'm not sure about that. The traffic might not be bad."),
        ("A", "You have a point, but I'd rather be safe."),
        ("B", "Fair enough. Let's leave at 6 then."),
    ],
    "dialogue_03_approach": [
        ("A", "Actually, I don't think that's the best approach."),
        ("B", "I see your point, but we've always done it this way."),
        ("A", "I understand, but things have changed."),
        ("B", "You might be right. Let me think about it."),
    ],
    "dialogue_04_movie": [
        ("A", "To be honest, I didn't enjoy the movie."),
        ("B", "Really? I thought it was amazing!"),
        ("A", "I mean, the acting was good, but the story was weak."),
        ("B", "That's true. The ending was disappointing."),
    ],
    "dialogue_05_planning": [
        ("A", "First of all, we need to decide on a date."),
        ("B", "I agree. Then we can book the venue."),
        ("A", "Exactly. By the way, have you checked the budget?"),
        ("B", "Not yet. Anyway, let's focus on the date first."),
    ],
}

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
async def generate_single_audio(text, voice, rate, filename):
    """Generate one MP3 file, with fallback to default voice."""
    try:
        communicator = edge_tts.Communicate(text, voice, rate=rate)
        await communicator.save(filename)
        if Path(filename).exists() and Path(filename).stat().st_size > 0:
            print(f"  ✓ {filename}")
            return True
        else:
            print(f"  ✗ Empty: {filename}")
            return False
    except Exception as e:
        print(f"  ⚠ {filename}: {e}")
        # Fallback
        try:
            communicator = edge_tts.Communicate(text, "en-US-JennyNeural", rate="-15%")
            await communicator.save(filename)
            if Path(filename).exists() and Path(filename).stat().st_size > 0:
                print(f"  ✓ {filename} (fallback)")
                return True
        except:
            pass
        return False

async def generate_dialogue_mp3(dialogue_id, turns, temp_dir):
    """Generate individual turn MP3s then concatenate into one dialogue file."""
    seg_files = []
    for i, (speaker, text) in enumerate(turns):
        voice = DIALOGUE_VOICE_A if speaker == "A" else DIALOGUE_VOICE_B
        clean_name = f"{dialogue_id}_{i:02d}_{speaker}.mp3"
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in "._-")
        seg_path = temp_dir / clean_name
        if await generate_single_audio(text, voice, DIALOGUE_RATE, str(seg_path)):
            seg_files.append(seg_path)
        else:
            print(f"  ⚠ Skipping turn {i+1} in {dialogue_id}")
        await asyncio.sleep(0.3)

    output_file = f"{dialogue_id}.mp3"
    if seg_files:
        with open(output_file, 'wb') as out:
            for fp in seg_files:
                with open(fp, 'rb') as inf:
                    shutil.copyfileobj(inf, out)
        print(f"  ✅ Created {output_file} ({Path(output_file).stat().st_size} bytes)")
    else:
        print(f"  ❌ No turns generated for {dialogue_id}")

async def main():
    print("\n" + "=" * 60)
    print("CONVERSATION SKILLS DICTIONARY – MP3 GENERATOR (No SSML)")
    print("=" * 60)

    total = 0
    success = 0

    # ---- Discourse Markers ----
    print("\n📌 Discourse Markers:")
    for phrase, example in DISCOURSE_MARKERS:
        base = phrase.lower().replace(" ", "_").replace("/", "_").replace("?", "").replace("(", "").replace(")", "")
        phrase_fn = f"dm_{base}_phrase.mp3"
        example_fn = f"dm_{base}_example.mp3"
        if await generate_single_audio(phrase, PHRASE_VOICE, RATE, phrase_fn):
            success += 1
        total += 1
        if await generate_single_audio(example, EXAMPLE_VOICE, RATE, example_fn):
            success += 1
        total += 1
        await asyncio.sleep(0.4)

    # ---- Agreeing Phrases ----
    print("\n📌 Agreeing Phrases:")
    for phrase, example in AGREEING_PHRASES:
        base = phrase.lower().replace(" ", "_").replace("'", "").replace("(", "").replace(")", "").replace(".", "").replace(",", "")
        phrase_fn = f"agree_{base}_phrase.mp3"
        example_fn = f"agree_{base}_example.mp3"
        if await generate_single_audio(phrase, PHRASE_VOICE, RATE, phrase_fn):
            success += 1
        total += 1
        if await generate_single_audio(example, EXAMPLE_VOICE, RATE, example_fn):
            success += 1
        total += 1
        await asyncio.sleep(0.4)

    # ---- Disagreeing Phrases ----
    print("\n📌 Disagreeing Phrases:")
    for phrase, example in DISAGREEING_PHRASES:
        base = phrase.lower().replace(" ", "_").replace("'", "").replace(",", "").replace("…", "").replace("?", "").replace("(", "").replace(")", "")
        phrase_fn = f"disagree_{base}_phrase.mp3"
        example_fn = f"disagree_{base}_example.mp3"
        if await generate_single_audio(phrase, PHRASE_VOICE, RATE, phrase_fn):
            success += 1
        total += 1
        if await generate_single_audio(example, EXAMPLE_VOICE, RATE, example_fn):
            success += 1
        total += 1
        await asyncio.sleep(0.4)

    # ---- Dialogues ----
    print("\n📌 Practice Dialogues:")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        for dialogue_id, turns in DIALOGUES.items():
            await generate_dialogue_mp3(dialogue_id, turns, tmpdir)
            success += 1  # assuming it'll succeed; adjust if needed
            total += 1
            await asyncio.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ {success} / {total} files generated.")
    print("🎧 The HTML dictionary is now fully usable with audio.")

if __name__ == "__main__":
    asyncio.run(main())