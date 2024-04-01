import random
import time
from typing import NoReturn, Optional, Tuple

from rich.console import Console
from rich.panel import Panel

from BotsOnRails.decorators import step_decorator_for_path
from BotsOnRails.rails import ExecutionPath
from faker import Faker

tree = ExecutionPath()
onboarding_agent_nodes = step_decorator_for_path(tree)

Faker.seed(random.randint(0, 100000))
fake = Faker()


@onboarding_agent_nodes(next_step='assign_a_new_title', path_start=True)
def get_name(*args, **kwargs) -> str:
    """
    Fetch the user's name to print up some rad biz cards.
    """
    name = input("What is your name, my friend?")
    return name


@onboarding_agent_nodes(wait_for_approval=True, next_step='print_up_business_card')
def assign_a_new_title(name: str, *args, **kwargs) -> Tuple[str, str]:
    """
    Use our super awesome 'AI' HR bot to assign you the job you'll be best at!
    """
    print(f"Let's assign you a job, {name}!")
    proposed_job = fake.job()
    print(f"You shall be (drumroll :-D)... ")
    time.sleep(1)
    print(f"{name} - `{proposed_job}`")
    print(f"Do you like it? Please say yes!")
    return proposed_job, "Is hungry"


@onboarding_agent_nodes()
def print_up_business_card(proposed_job_title: str, bob: str, *args,  tes: Optional[bool] = None, **kwargs) -> NoReturn:
    """
    THE most important part. Print some biz cards. I wonder what kind of card stock we'll get?
    """

    print(proposed_job_title)
    print(bob)
    print(tes)
    print(args)
    print(kwargs)

    name = fake.name()
    email = fake.email()
    phone = fake.phone_number()

    console = Console()
    business_card_content = f"[bold]{name}[/bold]\nJob: {proposed_job_title}\nEmail: {email}\nPhone: {phone}"
    panel = Panel(business_card_content, title="Business Card", expand=False)
    console.print(panel)


tree.compile(type_checking=True)
initial_results = tree.run()

like_it = input("Do you like your new job title? Please say yes! Type `yes` to print up some biz cards.")
if like_it.lower() == 'yes':
    tree.run_from_step(
        'assign_a_new_title',
        prev_execution_state=initial_results,
        has_approval=True
    )
else:
    print("Oh well... You can't please 'em all.")

print(tree.dump_json())
tree.visualize_via_graphviz("tree.dot")
