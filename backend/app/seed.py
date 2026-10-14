"""Synthetic demo data (fictional doctors, hospitals and products):  python -m app.seed"""
import random
from datetime import date, timedelta

from sqlalchemy import select

from app.core.security import hash_password
from app.db import Base, SessionLocal, engine
from app.models import HCP, FollowUp, Interaction, InteractionType, Product, Role, Sentiment, Tier, User

DOCTORS = [
    ("Anita Verma", "Cardiology", "Lakeview Heart Institute", "Mumbai", "A"), ("Rohan Iyer", "Cardiology", "Sunrise Hospital", "Bengaluru", "A"),
    ("Meera Nair", "Endocrinology", "City Care Medical Centre", "Chennai", "A"), ("Karan Malhotra", "Endocrinology", "Metro Diabetes Clinic", "Delhi", "B"),
    ("Priya Sharma", "Neurology", "Northfield Neuro Centre", "Delhi", "A"), ("Arjun Reddy", "Neurology", "Greenfield Hospital", "Hyderabad", "B"),
    ("Sana Qureshi", "Pulmonology", "Riverside Chest Clinic", "Pune", "B"), ("Vikram Desai", "Pulmonology", "Sunrise Hospital", "Bengaluru", "C"),
    ("Neha Kapoor", "Oncology", "Hope Cancer Institute", "Mumbai", "A"), ("Rahul Bose", "Oncology", "Eastern General Hospital", "Kolkata", "B"),
    ("Isha Menon", "Gastroenterology", "Lakeview Heart Institute", "Mumbai", "B"), ("Dev Patel", "Gastroenterology", "Pioneer Medical College", "Ahmedabad", "C"),
    ("Tanvi Joshi", "Dermatology", "SkinFirst Clinic", "Pune", "C"), ("Aditya Rao", "Cardiology", "Greenfield Hospital", "Hyderabad", "B"),
    ("Farah Khan", "General Medicine", "City Care Medical Centre", "Chennai", "C"), ("Manish Gupta", "General Medicine", "Metro Diabetes Clinic", "Delhi", "C"),
    ("Lakshmi Pillai", "Endocrinology", "Eastern General Hospital", "Kolkata", "B"), ("Sameer Kulkarni", "Neurology", "Pioneer Medical College", "Ahmedabad", "C"),
    ("Divya Singh", "Oncology", "Northfield Neuro Centre", "Delhi", "B"), ("Harsh Vora", "Pulmonology", "Hope Cancer Institute", "Mumbai", "C"),
    ("Ritu Banerjee", "Cardiology", "Eastern General Hospital", "Kolkata", "A"), ("Nikhil Jain", "General Medicine", "Riverside Chest Clinic", "Pune", "C"),
]
PRODUCTS = [("CardioMax", "Cardiovascular"), ("GlucoStable", "Diabetes"), ("NeuroCalm", "Neurology"), ("BreatheEasy", "Respiratory"),
            ("OncoShield", "Oncology"), ("GastroEase", "Gastro"), ("DermaClear", "Dermatology"), ("VitaBoost", "Nutrition")]
NOTES = {
    "positive": ["Doctor was receptive and asked for the clinical trial summary.", "Keen to start new patients on the product this month.",
                 "Positive discussion about dosing flexibility; agreed to a follow-up demo."],
    "neutral": ["Reviewed product literature; doctor will consider after the next conference.", "Short meeting, left samples and the brochure.",
                "Discussed formulary status; no commitment yet."],
    "negative": ["Raised concerns about side effects reported by two patients.", "Prefers a competitor product; cited pricing.",
                 "Unhappy about delayed sample delivery."],
}
CATS = {"Cardiology": "CardioMax", "Endocrinology": "GlucoStable", "Neurology": "NeuroCalm", "Pulmonology": "BreatheEasy",
        "Oncology": "OncoShield", "Gastroenterology": "GastroEase", "Dermatology": "DermaClear", "General Medicine": "VitaBoost"}


def seed(db) -> dict:
    if db.scalar(select(User)):
        return {"skipped": True}
    rnd = random.Random(42)
    manager = User(name="Maya Kulkarni", email="manager@crm.dev", hashed_password=hash_password("manager123"), role=Role.manager)
    reps = [User(name="Aarav Mehta", email="rep1@crm.dev", hashed_password=hash_password("rep12345"), role=Role.rep),
            User(name="Sneha Rao", email="rep2@crm.dev", hashed_password=hash_password("rep12345"), role=Role.rep)]
    db.add_all([manager, *reps])
    prods = {n: Product(name=n, category=c) for n, c in PRODUCTS}
    db.add_all(prods.values())
    db.flush()
    hcps = []
    for i, (n, sp, hosp, city, tier) in enumerate(DOCTORS):
        h = HCP(name=f"Dr. {n}", specialty=sp, hospital=hosp, city=city, tier=Tier(tier), assigned_rep_id=reps[i % 2].id)
        db.add(h)
        hcps.append(h)
    db.flush()
    today = date.today()
    n_it = 0
    for h in hcps:
        freq = {"A": 7, "B": 14, "C": 28}[h.tier.value]
        stale = rnd.random() < 0.25 and h.tier != Tier.C      # some important doctors are deliberately neglected, to show "at risk"
        day = 90
        while day > (45 if stale else 1):
            s = rnd.choices(["positive", "neutral", "negative"], [5, 3, 2])[0]
            it = Interaction(rep_id=h.assigned_rep_id, hcp_id=h.id, occurred_on=today - timedelta(days=day), type=rnd.choice(list(InteractionType)),
                             location=h.hospital, notes=rnd.choice(NOTES[s]), sentiment=Sentiment(s), source=rnd.choice(["form", "quick_log", "assistant"]),
                             next_steps="Send trial summary" if s == "positive" else "")
            it.products = list({prods[CATS[h.specialty]], *([rnd.choice(list(prods.values()))] if rnd.random() < 0.3 else [])})
            db.add(it)
            n_it += 1
            day -= max(2, int(rnd.gauss(freq, freq / 3)))
        if not stale and rnd.random() < 0.6:
            db.add(FollowUp(rep_id=h.assigned_rep_id, hcp_id=h.id, title=rnd.choice(["Share clinical trial summary", "Drop off samples", "Schedule product demo"]),
                            due_on=today + timedelta(days=rnd.randint(-6, 14))))
    db.flush()
    for it in db.scalars(select(Interaction)):
        from app.services.crm import make_summary
        it.summary = make_summary(it)
    db.commit()
    return {"hcps": len(hcps), "interactions": n_it}


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        print(seed(db))
    print("Manager: manager@crm.dev / manager123   Reps: rep1@crm.dev, rep2@crm.dev / rep12345")
