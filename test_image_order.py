from requests import GPT
import dotenv
dotenv.load_dotenv()
gpt = GPT()

print(gpt.send_images(["imgs/tests/red.JPG", "imgs/tests/green.JPG"], "Which image contains a green object? Refer to the images by number. The first image I send is 1, the second is 2. Only give the number without any symbols"))