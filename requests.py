import base64
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage


class GPT:
	def __init__(self) -> None:
		self.client = OpenAI()
		self.convo: list[ChatCompletionMessageParam] = []

	def send_message(self, message: str) -> str:
		"""Send text message to GPT-4o"""
		dict_message: list[ChatCompletionMessageParam] = [
			{"role": "user", "content": message}
		]
		response = self.client.chat.completions.create(
			model="gpt-4o",
			messages=dict_message + self.convo,
			temperature=0
		)
		response_message = response.choices[0].message
		self._save_message(response_message)
		return response_message.content or ""
	
	def send_image(self, image_filename: str, caption: str | None = None) -> str:
		"""Send image with optional caption to GPT-4o"""
		return self.send_images([image_filename], caption)

	def send_images(self, image_filenames: list[str], caption: str | None = None) -> str:
		"""Send images with optional caption to GPT-4o"""

		base64_images = [self._encode_image(image_filename) for image_filename in image_filenames]
		message: list[ChatCompletionMessageParam] = [
			{
				"role": "user",
				"content": [
				],
			}
		]
		if caption:
			message[0]["content"].append( # type: ignore
				{"type": "text", "text": caption}
			)
		for image in base64_images:
			message[0]["content"].append( # type: ignore
				{
					"type": "image_url",
					"image_url": {
						"url": f"data:image/jpeg;base64,{image}",
						"detail": "high",
					},
				})
		response = self.client.chat.completions.create(
			model="gpt-4o",
			messages=message + self.convo,
			temperature=0
		)
		response_message = response.choices[0].message
		self._save_message(response_message)
		return response_message.content or ""

	def clear_convo(self) -> None:
		"""Reset conversation to 0"""
		self.convo = []

	## Helper funcs
	def _encode_image(self, image_filename: str) -> str:
		with open(image_filename, "rb") as image_file:
			return base64.b64encode(image_file.read()).decode("utf-8")

	def _save_message(self, message: ChatCompletionMessage) -> None:
		self.convo.append({"role": message.role, "content": message.content})
