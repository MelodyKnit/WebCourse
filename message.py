class Message(list):

    def __init__(self, text: str = None):
        super().__init__()
        if text:
            self.text(text)

    def image(self, pic_md5: str):
        self.append({
            "msg_not_online_image": {
                "bytes_pic_md5": pic_md5
            },
            "uint32_elem_type": 3
        })
        return self

    def text(self, text: str):
        self.append({
            "msg_text": {
                "bytes_str": text
            },
            "uint32_elem_type": 1
        })
        return self

    def face(self, index: int):
        self.append({
            "msg_face": {
                "uint32_index": index
            },
            "uint32_elem_type": 2
        })
        return self

    def add_info(self, user_name: str):
        self.append({
            "msg_add_info": {
                "str_nick_name": user_name
            },
            "uint32_elem_type": 18
        })
        return self

