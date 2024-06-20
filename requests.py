import base64
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage

class GPT:
	def __init__(self) -> None:
		self.client = OpenAI()
		self.convo: list[ChatCompletionMessageParam] = []

	def send_message (self, message: str) -> str | None:
		"""Send text message to GPT-4o
		"""
		dict_message: list[ChatCompletionMessageParam] = [{
			"role": "user",
			"content": message
		}]
		response = self.client.chat.completions.create(
			model="gpt-4o",
			messages=dict_message + self.convo,
		)
		response_message = response.choices[0].message
		self._save_message(response_message)
		return response_message.content

	def send_image(self, image_filename: str, caption: str | None = None) -> str | None:
		"""Send image with optional caption to GPT-4o
		"""
		base64_image = self._encode_image(image_filename)
		message: list[ChatCompletionMessageParam] = [{
			"role": "user",
			"content": [
				{
					"type": "image_url",
					"image_url": {
						"url": f"data:image/jpeg;base64,{base64_image}",
						"detail": "low"
					}
				}
			]
		}]
		if caption:
			message[0]["content"].insert(0, { # type: ignore
					"type": "text",
					"text": caption
				})
		response = self.client.chat.completions.create(
			model="gpt-4o",
			messages=message + self.convo,
		)
		return response.choices[0].message.content

	def clear_convo (self):
		"""Reset conversation to 0"""
		self.convo = []

	## Helper funcs
	def _encode_image(self, image_filename: str) -> str:
		with open(image_filename, "rb") as image_file:
			return base64.b64encode(image_file.read()).decode('utf-8')
	
	def _save_message(self, message: ChatCompletionMessage) -> None:
		self.convo.append({
			"role": message.role,
			"content": message.content
		})
	
