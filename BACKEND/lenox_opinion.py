import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

def generate_lenox_opinion(analysis, additional_input, lenox_instance):
    llm = ChatOpenAI(temperature=0.7)

    # Generate Lenox Opinion: combining analysis, sentiment, and user-centric recommendation
    opinion_prompt = ChatPromptTemplate.from_template(
        "Here's what the chart analysis says:\n{analysis}\n"
        "And here's some additional context you gave:\n{additional_input}\n"
        "Now, let's boil it down. What's the overall market vibe? Summarize the key trends, patterns, and levels without repeating them too much. "
        "If the user is already holding this coin, should they keep holding or consider cashing out? "
        "If they're thinking about buying, should they dive in now or wait for a better deal? "
        "Finally, give a clear BUY, SELL, or HOLD recommendation with some flair."
    )

    opinion_chain = LLMChain(llm=llm, prompt=opinion_prompt)
    lenox_opinion = opinion_chain.run(analysis=analysis, additional_input=additional_input)

    logging.debug(f"Lenox Opinion Result: {lenox_opinion}")

    # Extract the main recommendation explicitly for both holders and potential buyers
    hold_or_sell = "HOLD"  # Default to HOLD if no clear signal is found for holders
    buy_or_wait = "WAIT"   # Default to WAIT if no clear signal is found for buyers
    
    if "SELL" in lenox_opinion.upper():
        hold_or_sell = "SELL"
    elif "BUY" in lenox_opinion.upper():
        buy_or_wait = "BUY"
    elif "WAIT" in lenox_opinion.upper():
        buy_or_wait = "WAIT"
    
    logging.debug(f"Hold or Sell Recommendation Extracted: {hold_or_sell}")
    logging.debug(f"Buy or Wait Recommendation Extracted: {buy_or_wait}")

    # Inject some personality into the final opinion, without redundancy
    final_opinion = f"{lenox_opinion}\n\n" \
                f"🚀 **Lenox's Take:** If you’re already holding this coin, my advice is to HOLD. " \
                f"Steady hands win the race. But if you’re thinking about buying, it might be better to WAIT for now. " \
                f"Keep a close eye on that resistance—patience in the crypto game is often rewarded. Stay sharp, and may your gains be glorious!"

    return {
        'lenox_opinion': final_opinion,
        'hold_or_sell': hold_or_sell,
        'buy_or_wait': buy_or_wait
    }
