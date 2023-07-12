#-*- coding: utf-8 -*-

from bgesdk import models

import json
import pytest


class TestModels:

    @pytest.mark.parametrize('attr', ['x'])
    def test_unknown_attribute(self, logger, attr):
        with pytest.raises(AttributeError):
            getattr(models.Model({}), attr)

    def test_json(self, logger):
        result = {
            "name": "Tom",
            "children": ["Lili", "Jay"],
            "detail": {
                "age": 32
            }
        }
        r = models.Model(result)
        assert result == r.json()
        s = r.dumps()
        assert isinstance(s, str)
        assert result == json.loads(s)
        s = json.dumps(result, cls=models.ModelEncoder)
        assert isinstance(s, str)
        assert result == json.loads(s)
