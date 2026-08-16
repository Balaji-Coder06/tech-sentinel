import unittest
from agent.utils.taxonomy import normalize_category
from agent.processors.classifier import ContentClassifier
from agent.models import RawItem

class TestCategoryTaxonomy(unittest.TestCase):
    def test_canonical_equivalents_normalized(self):
        # AI variations
        self.assertEqual(normalize_category("AI"), "ai")
        self.assertEqual(normalize_category("Artificial Intelligence"), "ai")
        self.assertEqual(normalize_category("artificial-intelligence"), "ai")
        self.assertEqual(normalize_category("machine learning"), "ai")
        self.assertEqual(normalize_category("ML"), "ai")
        self.assertEqual(normalize_category("deep_learning"), "ai")

        # Cloud variations
        self.assertEqual(normalize_category("Cloud"), "cloud")
        self.assertEqual(normalize_category("Cloud Computing"), "cloud")
        self.assertEqual(normalize_category("cloud-computing"), "cloud")
        self.assertEqual(normalize_category("Cloud Infrastructure"), "cloud")
        self.assertEqual(normalize_category("DevOps"), "cloud")
        self.assertEqual(normalize_category("Serverless"), "cloud")

        # Development variations
        self.assertEqual(normalize_category("Development"), "development")
        self.assertEqual(normalize_category("Software Development"), "development")
        self.assertEqual(normalize_category("software-dev"), "development")
        self.assertEqual(normalize_category("Programming"), "development")
        self.assertEqual(normalize_category("coding"), "development")
        self.assertEqual(normalize_category("Developer Tools"), "development")

        # Open Source variations
        self.assertEqual(normalize_category("Open Source"), "open_source")
        self.assertEqual(normalize_category("open-source"), "open_source")
        self.assertEqual(normalize_category("OSS"), "open_source")
        self.assertEqual(normalize_category("FOSS"), "open_source")

        # Cybersecurity variations
        self.assertEqual(normalize_category("Cybersecurity"), "cybersecurity")
        self.assertEqual(normalize_category("Cyber Security"), "cybersecurity")
        self.assertEqual(normalize_category("cyber-security"), "cybersecurity")
        self.assertEqual(normalize_category("Security"), "cybersecurity")
        self.assertEqual(normalize_category("infosec"), "cybersecurity")

        # Startups variations
        self.assertEqual(normalize_category("Startup"), "startups")
        self.assertEqual(normalize_category("Startups"), "startups")
        self.assertEqual(normalize_category("start-up"), "startups")
        self.assertEqual(normalize_category("venture"), "startups")

    def test_distinct_domains_not_merged(self):
        # AI and Cloud must remain distinct
        self.assertNotEqual(normalize_category("ai"), normalize_category("cloud"))
        self.assertNotEqual(normalize_category("cybersecurity"), normalize_category("development"))
        self.assertNotEqual(normalize_category("open_source"), normalize_category("startups"))

    def test_new_future_categories_preserved(self):
        # Novel distinct categories must form clean slugs
        self.assertEqual(normalize_category("Robotics"), "robotics")
        self.assertEqual(normalize_category("Quantum Computing"), "quantum_computing")
        self.assertEqual(normalize_category("Hardware & Embedded"), "hardware_embedded")

    def test_content_classifier_assigns_canonical_category(self):
        classifier = ContentClassifier()
        item = RawItem(
            title="Kubernetes 1.32 Cloud Architecture Guide",
            description="Scaling serverless cluster nodes in AWS and GCP",
            url="https://example.com/k8s-cloud",
            source_id="src_test",
            source_name="Cloud Blog"
        )
        cat, tags = classifier.classify(item)
        self.assertEqual(cat, "cloud")

if __name__ == "__main__":
    unittest.main()
