from trainer.study.checking import check


def test_parenthetical_and_to_prefix():
    assert check("be glad", "To be glad (to meet)")
    assert check("to be glad", "To be glad (to meet)")
    assert check("to be glad to meet", "To be glad (to meet)")


def test_alternatives():
    assert check("저", "저 (나)") and check("나", "저 (나)")
    assert check("person", "Person/people") and check("people", "Person/people")
    assert check("we", "We, our (my)") and check("my", "We, our (my)")
    assert check("mr", "Mr./Ms. (first name)") and check("mr./ms.", "Mr./Ms. (first name)")


def test_spacing_and_case():
    assert check("이름이뭐예요", "이름이 뭐예요?")
    assert check("the philippines", "The Philippines")


def test_please_prefix():
    assert check("sit down", "please sit down") and check("please sit down", "sit down")


def test_wrong_or_empty():
    assert not check("", "USA") and not check("canada", "USA")
