from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired, ValidationError

class ScanSettingsForm(FlaskForm):

    paper_size = RadioField('Paper Size', choices=[
        ('a4-portrait','A4 Portrait'),
        ('a5-portrait','A5 Portrait'),
        ('a5-landscape','A5 Landscape')],
        default='a4-portrait',
        validators=[DataRequired()])

    sides = RadioField('Sides', choices=[
        ('front','One side'),
        ('duplex','Both sides (front & back)')],
        default='duplex',
        validators=[DataRequired()])

    # \u2588 = unicode character 'FULL BLOCK'
    color = RadioField('Color', choices=[
        ('color','<span class="r">\u2588</span><span class="g">\u2588</span><span class="b">\u2588</span> Color'),
        ('grayscale','<span class="dark">\u2588</span><span class="gray">\u2588</span><span class="silver">\u2588</span> Grayscale')],
        default='color',
        validators=[DataRequired()])

    resolution = RadioField('Resolution', choices=[
        ('200','200'),
        ('300','300'),
        ('400','400')],
        default='200',
        validators=[DataRequired()])

    output_format = RadioField('Output Format', choices=[
        ('pdf','PDF'),
        ('jpg','JPEG file(s)'),
        ('pdf_and_jpg','PDF & JPEG')],
        default='pdf',
        validators=[DataRequired()])

    submit = SubmitField('Scan')
