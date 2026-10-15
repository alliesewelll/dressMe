import base64
import io
import json
import os
import unittest
from unittest.mock import patch
from PIL import Image
from fastapi import HTTPException
import ai_styling

class AIStylingTests(unittest.TestCase):
    def photo(self):
        output=io.BytesIO()
        Image.new('RGB',(1600,1200),(190,140,115)).save(output,format='PNG')
        return output.getvalue()

    def test_preprocessing_and_invalid_image(self):
        encoded=ai_styling.prepare_image(self.photo()).split(',')[1]
        with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
            self.assertEqual(image.size,(1024,768))
            self.assertEqual(image.format,'JPEG')
            self.assertFalse(image.getexif())
        with self.assertRaises(HTTPException): ai_styling.prepare_image(b'not an image')

    @patch.dict(os.environ,{'OPENAI_API_KEY':'test-only','STYLE_VISION_MODEL':'test-model'})
    @patch('ai_styling.httpx.post')
    def test_structured_model_response_and_request(self,post):
        result={'image_quality':'usable','observations':['Even light'],
                'palette_candidates':[{'palette':'Light Spring','reason':'Try warm light colors'}],
                'clothing_suggestions':['Try your linen shirt'], 'limitations':['Lighting can affect colors']}
        post.return_value.json.return_value={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(result)}]}]}
        output=ai_styling.analyze_image(self.photo(),{'wardrobe':[]})
        self.assertEqual(output['analysis'],result)
        request=post.call_args.kwargs['json']
        self.assertFalse(request['store'])
        self.assertEqual(request['model'],'test-model')
        self.assertTrue(request['text']['format']['strict'])
        result['palette_candidates'][0]['palette']='invented palette'
        post.return_value.json.return_value['output'][0]['content'][0]['text']=json.dumps(result)
        with self.assertRaises(HTTPException) as error: ai_styling.analyze_image(self.photo(),{})
        self.assertEqual(error.exception.status_code,502)

    @patch.dict(os.environ,{'OPENAI_API_KEY':'','STYLE_VISION_MODEL':''})
    @patch('ai_styling.httpx.post')
    def test_missing_config_never_calls_provider(self,post):
        with self.assertRaises(HTTPException) as error: ai_styling.analyze_image(self.photo(),{})
        self.assertEqual(error.exception.status_code,503)
        post.assert_not_called()
