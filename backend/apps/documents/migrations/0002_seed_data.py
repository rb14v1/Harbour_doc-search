"""
Idempotent demo data: one demo user plus a handful of sample documents
spanning three topics (cooking, hiking, personal finance), so the search
endpoint has something real to return out of the box.

Each document's embedding is computed with the SAME apps.common.ai.get_embedding
function used by the live API - with no OPENAI_API_KEY configured (the
default for this sandbox / a fresh clone), that means these seeded
documents get deterministic STUB vectors, not semantically meaningful ones.
That's expected: it still fully exercises storage + similarity_search end
to end. Once OPENAI_API_KEY is set, re-save these documents (e.g. via the
API) to get real embeddings - this migration does not re-run automatically.

get_or_create() on (user, title)/(email) keys makes repeat `migrate` runs
(including re-running after a fake-reset) a no-op instead of inserting
duplicates.
"""
from django.db import migrations

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"

DEMO_DOCUMENTS = [
    (
        "Mastering a Simple Weeknight Risotto",
        "Risotto rewards patience more than skill. Use short-grain Arborio or "
        "Carnaroli rice, toast it in butter for a minute before adding any "
        "liquid, and add warm stock one ladle at a time, stirring until each "
        "addition is absorbed before pouring the next. The constant stirring "
        "releases starch from the rice and is what gives risotto its "
        "characteristic creaminess without any cream at all. Finish off the "
        "heat with a knob of cold butter and grated Parmesan, and let it rest "
        "for two minutes before serving so it loosens to the right consistency.",
    ),
    (
        "Why Searing Meat Before Braising Matters",
        "Searing meat in a hot, dry pan before it goes into a braise is not "
        "about 'sealing in juices' - that's a myth. It matters because the "
        "Maillard reaction between amino acids and sugars at high heat creates "
        "hundreds of new flavor compounds that a slow, wet braise alone never "
        "produces. Pat the meat dry first, don't crowd the pan, and resist the "
        "urge to move the pieces until a proper crust has formed and releases "
        "on its own. Those browned bits left in the pan (the fond) should be "
        "deglazed with wine or stock and added back to the braising liquid.",
    ),
    (
        "Keeping Homemade Bread From Going Stale Too Fast",
        "Homemade bread without preservatives stales faster than store-bought "
        "loaves, but a few habits slow it down. Let the loaf cool completely "
        "before slicing, since trapped steam accelerates staling. Store it cut "
        "side down on a board at room temperature for a day or two rather than "
        "in the fridge, which actually speeds up starch retrogradation. For "
        "longer storage, slice and freeze it - a few seconds in a toaster "
        "brings frozen slices back to nearly fresh-baked texture.",
    ),
    (
        "Planning a Safe Multi-Day Hiking Itinerary",
        "A good multi-day hiking itinerary builds in slack rather than packing "
        "each day to its physical limit. Plan daily distances around the "
        "slowest hiker in the group, add buffer time for weather and water "
        "stops, and always know the location of bail-out points where you "
        "could exit the trail early if someone is injured or conditions turn. "
        "Share the itinerary with someone who is not on the trip, including an "
        "expected return time, so help can be sent if you don't check in.",
    ),
    (
        "Layering Clothing for Cold-Weather Hikes",
        "Effective layering for cold hikes is about managing moisture as much "
        "as warmth. A moisture-wicking base layer keeps sweat off the skin, an "
        "insulating mid-layer (fleece or synthetic puffy) traps warm air, and "
        "a waterproof, breathable shell blocks wind and precipitation. Avoid "
        "cotton entirely in cold conditions since it holds moisture and "
        "accelerates heat loss. Adjust layers before you start sweating "
        "heavily on climbs, not after, since a soaked base layer chills "
        "quickly the moment you stop moving.",
    ),
    (
        "Reading Trail Markers and Topographic Maps",
        "Topographic maps use contour lines to show elevation - lines packed "
        "tightly together mean steep terrain, while widely spaced lines mean "
        "gentle slopes. Combine map reading with a compass or GPS rather than "
        "relying on painted trail blazes alone, since blazes can be sparse, "
        "faded, or misleading at junctions. Before setting out, identify "
        "obvious handrails on the map - rivers, ridgelines, trails - that let "
        "you confirm your position at a glance without constant precise "
        "navigation.",
    ),
    (
        "What a Water Filter Actually Protects You From",
        "Most backcountry water filters remove bacteria and protozoa like "
        "Giardia through a physical membrane with pores small enough to "
        "block them, but many filters do not remove viruses, which are far "
        "smaller. In regions with significant human contamination risk, pair "
        "a filter with chemical treatment or use a filter explicitly rated "
        "for viruses. Filters also do nothing for dissolved chemical "
        "contaminants or heavy metals - those require a different treatment "
        "method entirely, such as activated carbon.",
    ),
    (
        "Building a Starter Emergency Fund Before Anything Else",
        "Before paying down low-interest debt or investing aggressively, most "
        "financial planners recommend building a starter emergency fund of "
        "roughly one month's essential expenses, then growing it toward three "
        "to six months over time. The purpose isn't growth, so it belongs in "
        "a boring, liquid account like a high-yield savings account, not in "
        "the stock market. Having this buffer in place prevents an unexpected "
        "car repair or medical bill from turning into new high-interest debt.",
    ),
    (
        "Why Compound Growth Rewards Starting Early",
        "A dollar invested at 25 has decades longer to compound than a dollar "
        "invested at 45, which is why starting early matters more than "
        "starting with a large sum. At a 7% average annual return, money "
        "roughly doubles every ten years, so an investment made twenty years "
        "earlier has had two extra doubling periods to grow. This is also why "
        "consistently investing smaller amounts on a regular schedule - "
        "dollar-cost averaging - tends to outperform waiting to invest a "
        "lump sum once market conditions feel 'right'.",
    ),
    (
        "Understanding the Difference Between a Budget and a Spending Plan",
        "A budget that only tracks where money went last month is a report, "
        "not a plan - it tells you nothing about what to do differently. A "
        "forward-looking spending plan instead assigns every dollar of "
        "upcoming income a job before the money arrives: fixed bills, "
        "savings goals, discretionary spending. This approach, sometimes "
        "called zero-based budgeting, forces trade-offs to be made "
        "deliberately in advance rather than discovered by surprise when a "
        "checking account balance runs low near the end of the month.",
    ),
]


def seed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Document = apps.get_model("documents", "Document")

    # Import at runtime (not module import time) so this migration never
    # fails to load if these modules change shape; also avoids importing
    # Django-app-dependent settings before django.setup() during tooling
    # that merely inspects migration graphs.
    from django.contrib.auth.hashers import make_password

    from apps.common.ai import get_embedding

    user, _created = User.objects.get_or_create(
        email=DEMO_EMAIL,
        defaults={
            "password": make_password(DEMO_PASSWORD),
            "first_name": "Demo",
            "last_name": "User",
            "is_active": True,
        },
    )

    for title, content in DEMO_DOCUMENTS:
        Document.objects.get_or_create(
            user=user,
            title=title,
            defaults={
                "content": content,
                "embedding": get_embedding(f"{title}\n{content}"),
            },
        )


def unseed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Document = apps.get_model("documents", "Document")

    titles = [title for title, _content in DEMO_DOCUMENTS]
    try:
        user = User.objects.get(email=DEMO_EMAIL)
    except User.DoesNotExist:
        return
    Document.objects.filter(user=user, title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, unseed_demo_data),
    ]
