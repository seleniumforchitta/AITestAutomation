import asyncio
import os
from browser_use import ActionResult, BrowserConfig, Controller
from browser_use.agent.service import Agent 
from langchain_google_genai import ChatGoogleGenerativeAI 
from pydantic import BaseModel, SecretStr 
from config import GEMINI_API_KEY  # Import the API key from config.py

class CheckoutResults(BaseModel):
    login_status : str
    cart_status: str
    checkout_status: str
    total_update_status: str
    delivery_location_ststus: str
    confirmation_message: str

controller = Controller(output_model=CheckoutResults) 


# The step that is not working through AI will handled here. 
@controller.action('Get Attribute and url of the page') # To tie the function with the controller. It will just check the meaning of the senetencse to connect with the step, exact words are not needed. 
async def get_attr_url(browser: BrowserConfig): # It will use playwright browser internally
    page = await browser.get_current_page()
    current_url = page.url
    attr = await page.get_by.text("Shop Name").get_attribute('class')
    print(current_url)
    return ActionResult(extracted_content=f'current url is {current_url} and attribute is {attr}')
    
    
# Sometime it is not going to the exact website directly. It is searching in google & trying by self. 
# But we can direct here - so that it will directly visit the url. So this is a fallback mechanism for opening browser step
@controller.action('open base website')
async def open_website(browser: BrowserConfig):
    page = await browser.get_current_page()
    await page.goto('https://rahulshettyacademy.com/loginpagePractise/')
    return ActionResult(extracted_content='browser opened')

# Note - Even if you remove above 2 methods - AI will run the complete test by itself. These methods are created only to remove test flakiness. 
    
async def SiteValidation(): # All the browser used commands & functions are asynchronous, so this method is asynchronous
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY  # Use the imported API key
    # You can visit https://aistudio.google.com/apikey , select llm model as gemini-2.0-flash-exp and generate API Key. it is FREE for now & place the API key in config.py
    task = (
        'Important : I am UI Automation tester validating the tasks'
        'Open website https://rahulshettyacademy.com/loginpagePractise/'
        'Login with username and password. Login Details available in the same page'
        'Get Attribute and url of the page' # This is the step for which fallback mechanism is created i.e. if AI Fails 
        'After login, select first 2 products and add them to cart.'
        'Then checkout and store the total value you see in screen'
        'Increase the quantity of any product and check if total value update accordingly'
        'checkout and select country, agree terms and purchase '
        'verify thankyou message is displayed'
    )
    api_key = os.environ["GEMINI_API_KEY"]
    # Instead og Gemini we can use  Open AI also. But it is paid for now. 
    llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp' , api_key=SecretStr(api_key))
    # llm = ChatOpenAI(model='gpt-4o-mini')
    agent = Agent(task, llm, controller=controller, use_vision=True) # use_vision will help to capture screenshot
    history = await agent.run()
    history.save_to_file('agentresults.json') # Saving the o/p json to a file
    test_result = history.final_result()
    # Now conver the test result into JSON
    validated_result = CheckoutResults.model_validate_json(test_result)
    print(validated_result)
    
    assert validated_result.confirmation_message == "Thank you! Your order will be delivered in next few weeks :-)."
    assert validated_result.cart_status in ["2 items", "2 items in cart"]
    assert validated_result.checkout_status in ["Checkout successful", "Completed"]
    assert validated_result.delivery_location_status == "India"

asyncio.run(SiteValidation())