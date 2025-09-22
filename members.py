import json
import random
import time
from collections import defaultdict, deque
from datetime import datetime


# rematching happens every regular interval (month) or everytime a new person added or removed

class Member:
    def __init__(self, name, email:str, capacity=1, role="unknown", match=None, prev_match=None):
        self.name = name
        self.email = email
        self.id = email
        self.capacity = capacity # capacity == 0 => not interested / not required in the buddy program
        self.prev_match = prev_match
        self.match = match # id of the matched partner
        self.role = role
        self.unmatched = True

    def update_capacity(self, new_capacity):
        self.capacity = new_capacity

    def update_match(self, new_match):
        # self.prev_match = self.match  # it is already done in unmatched step
        self.match = new_match

    def update_role(self, new_role):
        self.role = new_role

    def to_json(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4
        )


class MemberEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class Group:
    def __init__(self, gr_name, pi_name=None, gr_email=None, member_list=None):
        self.group_name = gr_name
        self.pi_name = pi_name
        self.group_email = gr_email
        self.last_shuffled = None
        self.mem_dict = defaultdict()
        self.dummy = Member("Dummy", "dummy@dummymail.org", capacity=0, role="dummy")
        self.dirty_pair_state = True  # True -> re-matching needs to be done, (used for add or remove members)
        self.active_member_ids = []
        self.matching_counter = 0  # keeps track of number of times the matching algorithm runs
        self.group_a, self.group_b = deque([]), deque([])
        if member_list is None:
            member_list = [self.dummy]
        else:
            member_list = member_list + [self.dummy]
        self.total_count, self.active_count = self.build_member_dict(member_list)
        self.active_member_ids = self.get_active_members_ids(shuffle=True)
        self.split_group(self.active_member_ids)
        self.fix_odd_even()


    def member_exists(self, email):
        mem_id = email
        if mem_id in self.mem_dict:
            return mem_id
        else:
            return None

    def build_member_dict(self, mem_list):
        active = 0
        if mem_list:
            for member in mem_list:
                if member.id not in self.mem_dict:
                    self.mem_dict[member.id] = member
                    if member.capacity > 0:
                        active += 1
        return len(mem_list), active

    def fix_odd_even(self):
        if self.active_count % 2 != 0:  # odd numbr of active elements
            if self.dummy.email in self.active_member_ids:  # number of actual persons is actually even, remove dummy
                self.update_member_capacity(self.dummy.email, 0)
            else:  #  number of actual persons is actually odd, add dummy
                self.update_member_capacity(self.dummy.email, 1)

    def add_member(self, name, email, capacity=1, role="unknown", match=None, prev_match=None):
        if not name or not email:
            return "name or email can't be empty or none"
        if not self.member_exists(email):
            self.dirty_pair_state = True
            new_member = Member(name, email, capacity=capacity, role=role, match=match, prev_match=prev_match)
            self.mem_dict[new_member.id] = new_member
            self.total_count += 1
            if new_member.capacity > 0:
                self.append_to_group(new_member.id, self.active_count)
                self.active_count += 1
                self.active_member_ids.append(new_member.id)  # delta addition will not be shuffled
                self.fix_odd_even()
            return f"member {email} added"
        else:
            return f"member {email} already exists, skipping"

    def remove_member(self, email):
        m = self.mem_dict.pop(self.member_exists(email), None)
        if m:
            self.dirty_pair_state = True
            self.total_count -= 1
            if m.capacity > 0:
                self.active_count -= 1
            if m.id in self.active_member_ids:
                self.active_member_ids.remove(m.id)
            self.remove_from_group(m.id)
            self.fix_odd_even()
            return f"member {email} removed"
        else:
            return f"member {email} doesn't exist, skipping"

    def update_member_capacity(self, email, new_capacity):
        mem_id = self.member_exists(email)
        if mem_id:
            old_capacity = self.mem_dict[mem_id].capacity
            self.mem_dict[mem_id].update_capacity(new_capacity)
            if new_capacity < 1 <= old_capacity and mem_id in self.active_member_ids:
                self.dirty_pair_state = True
                self.active_member_ids.remove(mem_id)
                self.remove_from_group(mem_id)
                self.active_count -= 1
            elif new_capacity >= 1 > old_capacity and mem_id not in self.active_member_ids:
                self.dirty_pair_state = True
                self.active_member_ids.append(mem_id)
                self.append_to_group(mem_id, self.active_count)
                self.active_count += 1
            self.fix_odd_even()
            return f"member {email}'s capacity updated to {new_capacity}"
        else:
            return f"member {email} doesn't exist, skipping"

    def update_member_role(self, email, new_role):
        mem_id = self.member_exists(email)
        if mem_id:
            self.mem_dict[mem_id].update_role(new_role)
            return f"member {email}'s role updated to {new_role}"
        else:
            return f"member {email} doesn't exist, skipping"

    def unmatch_all(self):
        for mem_id, member in self.mem_dict.items():
            member.unmatched = True
            member.prev_match = member.match
            member.match = None

    def update_match(self, mem1_id, mem2_id):
        self.mem_dict[mem1_id].update_match(mem2_id)
        self.mem_dict[mem1_id].unmatched = False
        self.mem_dict[mem2_id].update_match(mem1_id)
        self.mem_dict[mem2_id].unmatched = False

    def read_members_from_json(self, json_input, mode="file_path"):
        if mode == "file_path":
            with open(json_input, "rb") as json_file:
                json_data = json.load(json_file)
        elif mode == "json_string":
            json_data = json.loads(json_input)
        elif mode == "object":
            json_data = json_input
        else:
            raise ValueError(f"Json input mode {mode} is not supported. "
                             f"Please use either of: 'file_path', 'json_string', 'object'")

        if self.mem_dict: # already exists -> append
            for mem_data in json_data:  # delta portion will not be shuffled
                self.add_member(
                    mem_data.get("name", None),
                    mem_data.get("email", None),
                    mem_data.get("capacity", 1),
                    mem_data.get("role", "unknown"),
                    mem_data.get("match", None),
                    mem_data.get("prev_match", None)
                )
        else:  # build from scratch
            member_list = []
            for mem_data in json_data:
                member_list.append(
                    Member(
                        mem_data.get("name", None),
                        mem_data.get("email", None),
                        mem_data.get("capacity", 1),
                        mem_data.get("role", "unknown"),
                        mem_data.get("match", None),
                        mem_data.get("prev_match", None)
                    )
                )
            self.total_count, self.active_count = self.build_member_dict(member_list)
            self.active_member_ids = self.get_active_members_ids(shuffle=True)
            self.split_group(self.active_member_ids)
        self.fix_odd_even()

    def get_all_members_json(self, output_path=None, list_form=True):
        if list_form:
            mem_collection = self.mem_dict_to_mem_list()
        else:
            mem_collection = self.mem_dict
        if output_path:
            with open(output_path, "w") as json_file:
                json.dump(mem_collection, json_file, indent=4, cls=MemberEncoder)
        return json.dumps(mem_collection, indent=4, cls=MemberEncoder)

    def get_all_matches(self, output_path=None, fmt="json"):
        matches = defaultdict()
        for mem_id, member in self.mem_dict.items():
            if member.unmatched :
                matches[f"{member.name} ({member.email})"] = None
            else:
                matched_member = self.mem_dict[member.match]
                matches[f"{member.name} ({member.email})"] = f"{matched_member.name} ({matched_member.email})"
        if fmt == "json":
            if output_path:
                with open(output_path, "w") as json_file:
                    json.dump(matches, json_file, indent=4)
            return json.dumps(matches, indent=4)
        elif fmt == "txt":
            matches_txt = []
            for mem, mem_match in matches.items():
                matches_txt.append(f"{mem} <--> {mem_match}")
            matches_txt = "\n".join(matches_txt)
            if output_path:
                with open(output_path, "w") as txt_file:
                    txt_file.write(matches_txt)
            return matches_txt
        else:
            raise ValueError(f"output format {fmt} not supported. Use either 'json' or 'txt'")

    def mem_dict_to_mem_list(self):
        mem_list = [member for _, member in self.mem_dict.items()]
        return mem_list

    def get_all_pair_set(self):
        pairs = set()
        for mem_id, member in self.mem_dict.items():
            pairs.add((mem_id, member.match))
        return pairs

    def append_to_group(self, mem_id, counter):
        if self.dummy.email == mem_id:
            if len(self.group_b) > len(self.group_a):
                self.group_a.append(mem_id)
            elif len(self.group_a) > len(self.group_b):
                self.group_b.append(mem_id)
        else:
            if len(self.group_b) > len(self.group_a):
                self.group_a.append(mem_id)
            elif len(self.group_a) > len(self.group_b):
                self.group_b.append(mem_id)
            elif self.dummy.email in self.group_a:
                self.group_a.append(mem_id)
            elif self.dummy.email in self.group_b:
                self.group_b.append(mem_id)
            elif counter % 2 == 0:
                self.group_a.append(mem_id)
            else:
                self.group_b.append(mem_id)

    def remove_from_group(self, mem_id):
        if (self.dummy.email == mem_id) or (not self._is_same_group(self.dummy.email, mem_id)):
            if mem_id in self.group_a:
                self.group_a.remove(mem_id)
            if mem_id in self.group_b:
                self.group_b.remove(mem_id)
        else:
            # exchange groups with same idx (pair or match)
            idx = self.group_a.index(mem_id) if mem_id in self.group_a else self.group_b.index(mem_id)
            var = self.group_a[idx]
            self.group_a[idx] = self.group_b[idx]
            self.group_b[idx] = var
            # remove
            self.remove_from_group(mem_id)

    def get_active_members_ids(self, shuffle=False):
        active_members = []
        for k, v in self.mem_dict.items():
            if v.capacity > 0:
                active_members.append(k)
        if shuffle and active_members:
            random.seed(datetime.now().timestamp())
            random.shuffle(active_members)
        return active_members

    def split_group(self, member_ids):
        for idx, mem_id in enumerate(member_ids):
            self.append_to_group(mem_id, idx)

    def sparrow(self):  # split pair and random rotate
        # setup
        random.seed(datetime.now().timestamp())
        self.unmatch_all()
        self.fix_odd_even()
        assert len(self.group_a) == len(self.group_b) == self.active_count/2, "Both the groups must have equal number of persons"

        # rotate and match
        if self.matching_counter != 0:
            self.group_b.rotate(-1)
        matched_pairs = [(a, b) for a, b in zip(self.group_a, self.group_b)]
        for pair in matched_pairs:
            self.update_match(pair[0], pair[1])
        if self.matching_counter != 0: # exchange between group a and group b
            # idx = self.matching_counter % len(self.group_a)
            idx = random.randint(0, (self.active_count//2)-1)
            var = self.group_a[idx]
            self.group_a[idx] = self.group_b[idx]
            self.group_b[idx] = var

        # post match configuration
        self.dirty_pair_state = False
        self.matching_counter += 1
        self.last_shuffled = datetime.now()

    def _is_same_group(self, mem_id1, mem_id2):
        if (mem_id1 in self.group_a and mem_id2 in self.group_a) or (mem_id1 in self.group_b and mem_id2 in self.group_b):
            return True
        else:
            return False


if __name__ == "__main__":
    group = Group("TestGroup")
    with open("new_matched_data.json", "rb") as jsf:
        jsd = jsf.read().decode("utf-8")
    group.read_members_from_json(jsd, mode="json_string")
    for i in range(1024):
        if i == 9:
            # group.add_member("Nico", "nico@uni-tuebingen.de")
            group.add_member("Tuv", "tuv@yahoo.com")
        if i == 13:
            group.add_member("Xyz", "xyz@hotmail.com")
        if i == 17:
            group.remove_member(email="mno@uni-tuebingen.de")
            group.add_member("Qrs", "qrs@gmail.com")
        if i == 19:
            pass
        group.sparrow()
        print(f"matching_round: {i:03d}")
        print(group.get_all_matches(fmt="json"))
        print("**********************************************************************************")
