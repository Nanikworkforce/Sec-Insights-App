import json
from django.core.serializers import serialize
from pathlib import Path
from sec_app.models.company import Company
from sec_app.models.metric import FinancialMetric
from sec_app.models.chatlog import ChatLog
from django.core.management.base import BaseCommand
# JSONDecodeError is imported but unused, can be removed

CHUNK_SIZE = 10000
CHUNK_FILE = Path("sec_app/fixtures/all_data_chunks.jsonl")  # JSON lines format for recovery

class Command(BaseCommand):
    help = "Dump only new seed data to all_data.json (chunked with partial write support)"

    def handle(self, *args, **kwargs):
        Path("sec_app/fixtures").mkdir(parents=True, exist_ok=True)

        # Load already dumped primary keys from previous JSONL (if any)
        dumped_pks = {
            "sec_app.chatlog": set(),
            "sec_app.company": set(),
            "sec_app.financialmetric": set(),
        }

        if CHUNK_FILE.exists():
            with open(CHUNK_FILE, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                        dumped_pks[obj["model"]].add(obj["pk"])
                    except json.JSONDecodeError:
                        continue

        def dump_queryset_in_chunks(queryset, model_label):
            count = queryset.count()
            print(f"📦 Dumping {count} new {model_label.split('.')[-1]} (chunked)...")
            chunk_num = 0
            for start in range(0, count, CHUNK_SIZE):
                end = min(start + CHUNK_SIZE, count)
                chunk = queryset[start:end]
                chunk_num += 1
                print(f"   ➤ Chunk {chunk_num}: records {start + 1} to {end}")
                serialized = serialize("json", chunk, use_natural_foreign_keys=True)
                objects = json.loads(serialized)
                with open(CHUNK_FILE, "a") as f:
                    for obj in objects:
                        f.write(json.dumps(obj) + "\n")
                yield from objects

        for model in [ChatLog, Company, FinancialMetric]:
            model_label = f"sec_app.{model._meta.model_name}"
            print(f"🔍 Checking for new {model.__name__} records...")
            queryset = model.objects.exclude(pk__in=dumped_pks[model_label])
            if queryset.exists():
                yieldable = dump_queryset_in_chunks(queryset, model_label)
                for _ in yieldable:
                    pass  # Force generator to execute
            else:
                print(f"✅ No new {model.__name__} to dump.")

        # Combine all lines into final JSON file
        print("🧩 Assembling final all_data.json...")
        all_objects = []
        with open(CHUNK_FILE, "r") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    all_objects.append(obj)
                except json.JSONDecodeError:
                    continue

        with open("sec_app/fixtures/all_data.json", "w") as f:
            json.dump(all_objects, f, indent=2)

        print(f"✅ Dump complete. Total records: {len(all_objects)}")
