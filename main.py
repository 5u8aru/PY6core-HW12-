from collections import UserDict
from datetime import date
from pathlib import Path
import datetime
import pickle

N = 2


class Field:
    def __init__(self, value):
        self.__value = None
        self.value = value

    def __str__(self):
        return f'{self.value}'

    def __eq__(self, other):
        return self.value == other.value


class Name(Field):
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: str):
        self.__value = value


class Phone(Field):
    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: str):
        def is_code_valid(phone_code: str):
            if '06' in phone_code[:2] or '09' in phone_code[:2]:
                return True
            return False

        valid_phone = None
        phone_num = value.removeprefix('+')
        if phone_num.isdigit():
            if '0' in phone_num[0] and len(phone_num) == 10 and is_code_valid(phone_num[:3]):
                valid_phone = '+38' + phone_num
            if '380' in phone_num[:3] and len(phone_num) == 12 and is_code_valid(phone_num[2:5]):
                valid_phone = '+' + phone_num
        if valid_phone is None:
            raise ValueError(f'Wrong type of {value}')
        self.__value = valid_phone


class Birthday(Field):
    def __str__(self):
        if self.value is None:
            return 'No date'
        return f'{self.value:%d %b %Y}'

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: str):
        if value is None:
            self.__value = None
        else:
            try:
                self.__value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                try:
                    self.__value = datetime.datetime.strptime(value, '%d.%m.%Y').date()
                except ValueError:
                    raise DateError


class Record:
    def __init__(self, name: Name, phones=[], birthday=None):
        self.name = name
        self.phone_l = phones
        self.birthday = birthday

    def add_p(self, phone_num: Phone):
        self.phone_l.append(phone_num)

    def del_p(self, phone_num: Phone):
        self.phone_l.remove(phone_num)

    def change_p(self, phone_num: Phone, new_phone_num: Phone):
        self.phone_l.remove(phone_num)
        self.phone_l.append(new_phone_num)

    def days_to_hp(self, birthday: Birthday):
        if birthday.value is None:
            return None
        right_now = date.today()
        birthday_day = date(right_now.year, birthday.value.month, birthday.value.day)
        if birthday_day < right_now:
            birthday_day = date(right_now.year + 1, birthday.value.month, birthday.value.day)
        return (birthday_day - right_now).days

    def __str__(self):
        return f'User {self.name} - Numbers: {", ".join([phone_num.value for phone_num in self.phone_l])} ' \
               f'- Birthday: {self.birthday}'


class AddressBook(UserDict):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = Path(filename)
        if self.filename.exists():
            with open(self.filename, 'rb') as db:
                self.data = pickle.load(db)

    def save(self):
        with open(self.filename, 'wb') as db:
            pickle.dump(self.data, db)

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def iterator(self, func=None):
        i = 0
        index, print_block = 1, 'Page ' + str(i) + '\n'
        for record in self.data.values():
            if func is None or func(record):
                print_block += str(record) + '\n'
                if index < N:
                    index += 1
                else:
                    i += 1
                    yield print_block
                    index, print_block = 1, 'Page ' + str(i) + '\n'
        yield print_block


class DateError(Exception):
    ...


class InputError:
    def __init__(self, func):
        self.func = func

    def __call__(self, contacts, *args, ):
        try:
            return self.func(contacts, *args)
        except IndexError:
            result = 'Enter a name and phone!'
        except KeyError:
            result = 'Can`t find this user in list!'
        except ValueError:
            result = 'Phone number or birthday date is incorrect!'
        except DateError:
            return 'Wrong date type!'
        return result


def greet(*args):
    return "How can I help you?"


@InputError
def add(contacts, *args):
    name = Name(args[0])
    m_phone = Phone(args[1])
    if name.value in contacts:
        if m_phone in contacts[name.value].phone_l:
            return f'{name}`s contact has already had this number'
        else:
            contacts[name.value].add_p(m_phone)
            return f'Add phone {m_phone} to user {name}'
    else:
        if len(args) > 2:
            birthday = Birthday(args[2])
        else:
            birthday = Birthday(None)
        contacts[name.value] = Record(name, [m_phone], birthday)
        return f'Add user {name} with phone number {m_phone}'


@InputError
def add_data(contacts, *args):
    name, birthday = args[0], args[1]
    contacts[name].birthday = Birthday(birthday)
    return f'Birthday date {contacts[name].birthday} of {name} was added or changed'


@InputError
def days_to_birthday(contacts, *args):
    name = args[0]
    if contacts[name].birthday.value is None:
        return f'{name} has no birthday'
    return f'{contacts[name].days_to_hp(contacts[name].birthday)} until {name}`s birthday'


@InputError
def change(contacts, *args):
    name, prev_phone, new_phone = args[0], args[1], args[2]
    contacts[name].change_p(Phone(prev_phone), Phone(new_phone))
    return f"{name}`s number changed from {Phone(prev_phone)} to {new_phone}"


@InputError
def phone(contacts, *args):
    name = args[0]
    return contacts[name]


@InputError
def delete_phone(contacts, *args):
    name, m_phone = args[0], args[1]
    contacts[name].del_p(Phone(m_phone))
    return f'{name}`s phone {m_phone} was deleted'


def search(contacts, *args):
    def find_sub(record):
        return subst.lower() in record.name.value.lower() or \
               any(subst in phone.value for phone in record.phone_l) or \
               (record.birthday.value is not None and subst in record.birthday.value.strftime('%d.%m.%Y'))

    subst = args[0]
    res = f'List of users with \'{subst.lower()}\' in data:\n'
    page = contacts.iterator(find_sub)
    for el in page:
        res += f'{el}'
    return res


def show_all(contacts, *args):
    if not contacts:
        return 'Empty'
    else:
        res = ''
        page = contacts.iterator()
        for el in page:
            res += f'{el}'
        return res


def goodbye(contacts, *args):
    contacts.save()
    print("Good bye!")
    return None


COMMANDS = {'hello': greet, 'add': add, 'change': change, 'phone': phone, 'show all': show_all,
            'good bye': goodbye, 'exit': goodbye, 'close': goodbye, 'delete': delete_phone,
            'birthday': add_data, 'days': days_to_birthday, 'search': search}


def main():
    contacts_list = AddressBook(filename='book.dat')
    while True:
        user_command = input('>>> ')
        for k, v in COMMANDS.items():
            if k in user_command.lower():
                args = user_command[len(k):].split()
                result = COMMANDS[k](contacts_list, *args)
                if result is None:
                    exit()
                print(result)
                break
        else:
            print('Unknown command! Enter again!')


if __name__ == '__main__':
    main()
