import crawl4ai

class ScrapingAgent:
	"""
	ScrapingAgent uses crawl4ai to crawl and extract data from websites.
	"""
	def __init__(self, config=None):
		self.config = config or {}

	async def run(self, task_description: str) -> str:
		"""
		Run a scraping task using crawl4ai.
		Args:
			task_description: Should contain the URL and optionally extraction instructions.
		Returns:
			Extracted data as a string (JSON or text summary)
		"""
		# Simple parsing: expect 'Crawl <url> and extract <what>'
		import re
		url_match = re.search(r'(https?://\S+)', task_description)
		if not url_match:
			return "No URL found in task description."
		url = url_match.group(1)

		# Optionally extract what to extract
		what_match = re.search(r'extract (.+)', task_description, re.IGNORECASE)
		extract_what = what_match.group(1) if what_match else None

		# Use crawl4ai to crawl the URL
		try:
			# You can customize crawl4ai parameters as needed
			results = crawl4ai.crawl(url, max_depth=1, return_format="json")
			# Optionally filter results based on extract_what
			if extract_what:
				# Simple filter: look for extract_what in text content
				filtered = [page for page in results['pages'] if extract_what.lower() in page.get('text', '').lower()]
				return str(filtered) if filtered else f"No content found for '{extract_what}'."
			return str(results)
		except Exception as e:
			return f"Scraping failed: {str(e)}"
