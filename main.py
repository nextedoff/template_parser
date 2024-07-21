from parsers import TemplateParser
import json

def main():
    path = "templates/mistralai_template_chat.txt"
    prev_q = [{'role': 'user', 'content': 'What is included in my Northwind Health Plus plan that is not in standard?'}, {'role': 'assistant', 'content': ' Your Northwind Health Plus plan includes virtual care services [Northwind_Standard_Benefits_Details.pdf#page=56], out-of-network services [Northwind_Standard_Benefits_Details.pdf#page=71], and emergency services, both in-network and out-of-network [Benefit_Options.pdf#page=3]. These services are not included in the standard plan. The standard plan does not cover mental health and substance abuse coverage, or services that are not medically necessary, such as cosmetic procedures and elective treatments [Northwind_Standard_Benefits_Details.pdf#page=56,71].'}]
    template_parser = TemplateParser()
    content = template_parser.read(path=path)
    rendered = template_parser.render_template(template=content["body"], sources=["test1: It is going to rain tomorrow.", "test2: It is sunny", "test3: hello world"], question="Is it good weather today?", past_questions=prev_q)
    dict_mess = template_parser.build_messages(rendered)
    print(dict_mess)
    
if __name__ == "__main__":
    main()