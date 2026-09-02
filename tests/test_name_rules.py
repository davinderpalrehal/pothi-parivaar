from app.services.name_rules import (
    AuthorName,
    HonorificRule,
    author_short_form,
    joined_short_forms,
    split_author_string,
)

SEEDISH = [
    HonorificRule(tokens=("Dr",), role="prefix", abbreviation="Dr."),
    HonorificRule(tokens=("Bhai", "Sahib", "Bhai"), role="prefix", abbreviation="BHB"),
    HonorificRule(tokens=("ji",), role="suffix", abbreviation=""),
]


def test_split_examples_from_name_rules():
    assert split_author_string("Dale Carnegie") == [
        AuthorName(first_name="Dale", last_name="Carnegie")
    ]
    assert split_author_string("Dale B. Carnegie") == [
        AuthorName(first_name="Dale", last_name="Carnegie", middle_name="B.")
    ]
    assert split_author_string("John Ronald Reuel Tolkien") == [
        AuthorName(first_name="John", last_name="Tolkien", middle_name="Ronald Reuel")
    ]
    assert split_author_string("Dale Carnegie, Jane Doe") == [
        AuthorName(first_name="Dale", last_name="Carnegie"),
        AuthorName(first_name="Jane", last_name="Doe"),
    ]
    assert split_author_string("D. Carnegie") == [
        AuthorName(first_name="D.", last_name="Carnegie")
    ]
    assert split_author_string("Plato") == [
        AuthorName(first_name="Plato", last_name=" ")
    ]
    assert split_author_string("Unknown Author") == [
        AuthorName(first_name="Unknown", last_name="Author")
    ]
    assert split_author_string("") == []
    assert split_author_string(None) == []


def test_short_form_and_joined_display():
    assert author_short_form("Dale", "Carnegie") == "D. Carnegie"
    assert author_short_form("Plato", " ") == "Plato"
    assert author_short_form("Madonna", " ") == "Madonna"
    assert author_short_form("Cher", " ") == "Cher"
    assert joined_short_forms(
        [
            AuthorName(first_name="Dale", last_name="Carnegie"),
            AuthorName(first_name="Jane", last_name="Doe"),
        ]
    ) == "D. Carnegie, J. Doe"
    assert joined_short_forms(
        [
            AuthorName(first_name="Plato", last_name=" "),
            AuthorName(first_name="Jane", last_name="Doe"),
        ]
    ) == "Plato, J. Doe"


def test_split_keeps_titles_in_name_parts():
    assert split_author_string("Dr. Davinder Singh") == [
        AuthorName(first_name="Dr.", last_name="Singh", middle_name="Davinder")
    ]
    assert split_author_string("Bhai Sahib Bhai Vir Singh ji") == [
        AuthorName(
            first_name="Bhai",
            last_name="ji",
            middle_name="Sahib Bhai Vir Singh",
        )
    ]


def test_short_form_peels_honorifics_including_middle():
    assert (
        author_short_form("Dr.", "Singh", "Davinder", SEEDISH) == "Dr. D. Singh"
    )
    assert (
        author_short_form("Bhai", "ji", "Sahib Bhai Vir Singh", SEEDISH)
        == "BHB V. Singh"
    )
    assert author_short_form("Dale", "Carnegie", None, SEEDISH) == "D. Carnegie"
    assert author_short_form("Plato", " ", None, SEEDISH) == "Plato"
    assert joined_short_forms(
        [
            AuthorName(first_name="Dr.", last_name="Singh", middle_name="Davinder"),
            AuthorName(first_name="Jane", last_name="Doe"),
        ],
        SEEDISH,
    ) == "Dr. D. Singh, J. Doe"
